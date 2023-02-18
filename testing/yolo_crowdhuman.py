import torch

save_path = "crowdhuman_yolov5m.pt"
image_path = "C:\\Users\\hbw30\\Downloads\\python.jpg"

model = torch.hub.load("ultralytics/yolov5", "custom", path="../backend/crowdhuman_yolov5m.pt")

results = model(image_path)

results.show()

person_count = list(results.xyxyn[0][:,-1].numpy()).count(1.0)
print("Head count:", person_count)