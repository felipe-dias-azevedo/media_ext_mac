def human_size(num_bytes):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if num_bytes < 1000:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1000