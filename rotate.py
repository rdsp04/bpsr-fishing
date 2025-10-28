import cv2

# Load template
template_path = "images/1920x1080/fish/rockpea.png"
template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)

# Get dimensions
(h, w) = template.shape[:2]
center = (w // 2, h // 2)

# 45 degrees counterclockwise
M = cv2.getRotationMatrix2D(center, 45, 1.0)
rotated_template = cv2.warpAffine(template, M, (w, h))

# Optional: save the rotated template
cv2.imwrite("images/1920x1080/fish/rockpea_rotated.png", rotated_template)
