import cv2
import numpy as np

# 3D model points
MODEL_POINTS = np.array([
    (0.0, 0.0, 0.0),        # nose tip
    (0.0, -63.6, -12.5),   # chin
    (-43.3, 32.7, -26.0),  # left eye
    (43.3, 32.7, -26.0),   # right eye
    (-28.9, -28.9, -24.1), # left mouth
    (28.9, -28.9, -24.1)   # right mouth
])

# indices in mediapipe landmarks
IDX = [1, 152, 33, 263, 61, 291]

def estimate_pose(landmarks, w, h):
    image_points = np.array([
        (landmarks.landmark[i].x * w,
         landmarks.landmark[i].y * h)
        for i in IDX
    ], dtype="double")

    focal = w
    center = (w / 2, h / 2)
    cam_matrix = np.array([
        [focal, 0, center[0]],
        [0, focal, center[1]],
        [0, 0, 1]
    ], dtype="double")

    dist_coeffs = np.zeros((4, 1))  # no lens distortion
    success, rvec, tvec = cv2.solvePnP(
        MODEL_POINTS, image_points, cam_matrix, dist_coeffs,
        flags=cv2.SOLVEPNP_ITERATIVE
    )

    rmat, _ = cv2.Rodrigues(rvec)
    angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)

    yaw = angles[1]
    pitch = angles[0]

    # Normalize pitch from [-180, 180] to centered around 0
    if pitch > 90:
        pitch = pitch - 180
    elif pitch < -90:
        pitch = pitch + 180

    return yaw, pitch
