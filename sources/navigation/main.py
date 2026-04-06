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

    # ==============================
    # MODELO
    # ==============================
    interpreter, input_details, output_details = load_model(MODEL_PATH)

    # ==============================
    # DATASET
    # ==============================
    image_paths = sorted([
        os.path.join(IMAGE_DIR, x)
        for x in os.listdir(IMAGE_DIR)
        if x.lower().endswith((".jpg", ".png"))
    ])

    print("Imágenes encontradas:", len(image_paths))

    # ==============================
    # ROI
    # ==============================
    roi_mask, roi_pts = trapezoid_roi((IMG_DATASET_H, IMG_DATASET_W))

    # ==============================
    # ROVER
    # ==============================
    rover = RoverClient()
    await rover.connect()

    # ==============================
    # LOOP
    # ==============================
    decision_buffer = []
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

        print("Clases detectadas:", mask.min(), "→", mask.max())

        nav_mask = create_navigation_mask(mask)

        # --------------------------
        # NAVEGACIÓN
        # --------------------------
        decision, c, l, r = decide_direction(nav_mask, roi_mask)

        decision_buffer.append(decision)

        # --------------------------
        # SLAM
        # --------------------------
        integrate_observation(mask)

        # --------------------------
        # DECISIÓN FINAL
        # --------------------------
        if len(decision_buffer) == FRAMES_PER_DECISION:

            final_decision = max(set(decision_buffer), key=decision_buffer.count)

            # SLAM interno (simulación)
            move_rover(final_decision)

            # ROVER REAL
            await rover.send_command(final_decision)

            print(
                f"Frame {idx} | "
                f"centro={c:.2f} izquierda={l:.2f} derecha={r:.2f} | "
                f"DECISION={final_decision}"
            )

            decision_buffer = []

        # --------------------------
        # DEBUG VISUAL
        # --------------------------
        if DEBUG:

            color_mask = colorize_mask(mask)

            overlay = cv2.addWeighted(img, 0.6, color_mask, 0.4, 0)

            if roi_pts is not None:
                cv2.polylines(
                    overlay,
                    [roi_pts],
                    isClosed=True,
                    color=(255, 0, 255),
                    thickness=2
                )

            combined = np.hstack([img, color_mask, overlay])

            cv2.imshow("Segmentation", combined)

            slam_view = draw_slam()
            cv2.imshow("SLAM", slam_view)

            cv2.waitKey(1)

            if SAVE_IMAGES:
                out_path = os.path.join(SAVE_DIR, f"frame_{idx:04d}.png")
                cv2.imwrite(out_path, combined)

                final_map = draw_slam()
                cv2.imwrite("slam_final.png", final_map)

                np.savetxt("full_map_classes.csv", grid, fmt="%d", delimiter=",")

    # ==============================
    # RESULTADOS
    # ==============================
    end = time.time()

    total_time = end - start
    fps = len(image_paths) / total_time

    print("\n==== RESULTADOS ====")
    print("Imágenes:", len(image_paths))
    print("Tiempo:", round(total_time, 2), "s")
    print("FPS:", round(fps, 2))
    print("ms/frame:", round(1000 / fps, 2))

    # ==============================
    # CIERRE
    # ==============================
    await rover.close()
    cv2.destroyAllWindows()


# ==============================
# ENTRY POINT
# ==============================
if __name__ == "__main__":
    asyncio.run(main())