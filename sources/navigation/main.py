import os
import cv2
import time
import asyncio
import numpy as np

from slam import grid
from config import *
from model import load_model, infer
from perception import preprocess, create_navigation_mask, trapezoid_roi
from navigation import decide_direction
from slam import integrate_observation, move_rover
from visualization import colorize_mask, draw_slam
from rover_ws import RoverClient


async def main():

    interpreter, input_details, output_details = load_model(MODEL_PATH)

    image_paths = sorted([
        os.path.join(IMAGE_DIR, x)
        for x in os.listdir(IMAGE_DIR)
        if x.lower().endswith((".jpg", ".png"))
    ])

    print("Imágenes encontradas:", len(image_paths))

    roi_mask, roi_pts = trapezoid_roi((IMG_DATASET_H, IMG_DATASET_W))

    rover = RoverClient()
    await rover.connect()


    decision_buffer = []
    last_command = "nav_ADELANTE"

    start = time.time()

    for idx, path in enumerate(image_paths):

        img = cv2.imread(path)

        # --------------------------
        # PERCEPCIÓN
        # --------------------------
        model_img = preprocess(img, input_details)

        mask = infer(
            interpreter,
            input_details,
            output_details,
            model_img,
            (IMG_DATASET_W, IMG_DATASET_H)
        )

        nav_mask = create_navigation_mask(mask)

        # --------------------------
        # DECISIÓN
        # --------------------------
        final_step_decision = rover.compute_decision(nav_mask, roi_mask)

        # --------------------------
        # SLAM
        # --------------------------
        integrate_observation(mask)

        # --------------------------
        # CONTROL
        # --------------------------
        if final_step_decision.startswith("sens_"):

            command = final_step_decision
            decision_buffer = []

            print(f"Frame {idx} | EVASION | DECISION={command}")

        else:

            decision_buffer.append(final_step_decision)

            if len(decision_buffer) == FRAMES_PER_DECISION:

                # filtro simple anti-oscilación
                if decision_buffer.count(decision_buffer[-1]) > len(decision_buffer)//2:
                    command = decision_buffer[-1]
                else:
                    command = last_command

                decision_buffer = []

                print(f"Frame {idx} | DECISION={command}")

            else:
                command = last_command

        # --------------------------
        # SLAM MOVIMIENTO
        # --------------------------
        slam_decision = command.replace("sens_", "").replace("nav_", "")
        move_rover(slam_decision)

        # --------------------------
        # ACTUALIZAR COMANDO (NO enviar aquí)
        # --------------------------
        rover.current_command = command
        last_command = command

        # --------------------------
        # DEBUG
        # --------------------------
        if DEBUG:

            color_mask = colorize_mask(mask)
            overlay = cv2.addWeighted(img, 0.6, color_mask, 0.4, 0)

            if roi_pts is not None:
                cv2.polylines(overlay, [roi_pts], True, (255, 0, 255), 2)

            combined = np.hstack([img, color_mask, overlay])

            cv2.imshow("Segmentation", combined)
            cv2.imshow("SLAM", draw_slam())
            cv2.waitKey(1)

        await asyncio.sleep(0.3)

    end = time.time()

    total_time = end - start
    fps = len(image_paths) / total_time

    print("\n==== RESULTADOS ====")
    print("FPS:", round(fps, 2))

    await rover.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    asyncio.run(main())