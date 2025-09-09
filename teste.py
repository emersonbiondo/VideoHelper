import torch

if torch.cuda.is_available():
    print("A GPU está disponível!")
    gpu_count = torch.cuda.device_count()
    print(f"Número de GPUs: {gpu_count}")
    for i in range(gpu_count):
        print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
else:
    print("A GPU não está disponível. O processamento será feito pela CPU.")