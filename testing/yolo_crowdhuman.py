import torch
import cv2

save_path = "crowdhuman_yolov5m.pt"
image_path = "queue_2.jpg"

yolo = torch.hub.load("ultralytics/yolov5", "custom", path="crowdhuman_yolov5m.pt")
yolo.conf = 0.25

def infer_frame(img,model):
    results=model(img)
    return results

ans=infer_frame(cv2.imread(image_path),yolo)
# ans.show()

person_count = list(ans.xyxyn[0][:,-1].numpy()).count(1.0)
print("Head count:", person_count)