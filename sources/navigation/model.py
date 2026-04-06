import tflite_runtime.interpreter as tflite

def load_model(path):
    interpreter = tflite.Interpreter(model_path=path, num_threads=8)
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    return interpreter, input_details, output_details


def infer(interpreter, input_details, output_details, model_img, resize_shape):
    import cv2
    import numpy as np

    interpreter.set_tensor(input_details[0]["index"], model_img)
    interpreter.invoke()

    output = interpreter.get_tensor(output_details[0]["index"])[0]

    mask = np.argmax(output, axis=-1)

    mask = cv2.resize(
        mask.astype(np.uint8),
        resize_shape,
        interpolation=cv2.INTER_NEAREST
    )

    return mask