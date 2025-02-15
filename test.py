import os
import shutil

# Mapping: key là id ban đầu, value là id mới
mapping = {7: 0, 11: 1, 5: 2}
selected_ids = set(mapping.keys())

# Các split cần xử lý
splits = ['./datasets_goc/train', './datasets_goc/valid', './datasets_goc/test']
# Thư mục dataset mới sẽ được copy ra
output_dir = 'filtered_dataset'

for split in splits:
    # Đường dẫn folder images và labels trong dataset gốc
    src_images_dir = os.path.join(split, 'images')
    src_labels_dir = os.path.join(split, 'labels')
    
    # Đường dẫn folder images và labels trong dataset mới
    dst_images_dir = os.path.join(output_dir, split, 'images')
    dst_labels_dir = os.path.join(output_dir, split, 'labels')
    
    # Tạo các thư mục nếu chưa tồn tại
    os.makedirs(dst_images_dir, exist_ok=True)
    os.makedirs(dst_labels_dir, exist_ok=True)
    
    # Duyệt qua các file label trong folder labels
    for label_file in os.listdir(src_labels_dir):
        if not label_file.endswith('.txt'):
            continue
        
        src_label_path = os.path.join(src_labels_dir, label_file)
        with open(src_label_path, 'r') as f:
            lines = f.readlines()
        
        new_lines = []
        for line in lines:
            parts = line.strip().split()
            # Giả sử định dạng YOLO: class x_center y_center width height
            if len(parts) < 5:
                continue
            try:
                orig_id = int(parts[0])
            except ValueError:
                continue
            
            # Chỉ giữ lại các dòng có class là Speed Limit cần chọn
            if orig_id in selected_ids:
                new_id = mapping[orig_id]
                # Ghi đè id ban đầu bằng id mới
                new_line = " ".join([str(new_id)] + parts[1:]) + "\n"
                new_lines.append(new_line)
        
        # Nếu file label có chứa ít nhất 1 dòng phù hợp thì copy file ảnh và label tương ứng
        if new_lines:
            # Ghi file label mới vào dataset mới
            dst_label_path = os.path.join(dst_labels_dir, label_file)
            with open(dst_label_path, 'w') as f:
                f.writelines(new_lines)
            
            # Xác định tên file ảnh tương ứng (chỉ khác phần mở rộng)
            image_file = label_file[:-4] + '.jpg'
            src_image_path = os.path.join(src_images_dir, image_file)
            dst_image_path = os.path.join(dst_images_dir, image_file)
            
            if os.path.exists(src_image_path):
                shutil.copy2(src_image_path, dst_image_path)
            else:
                print(f"Warning: File ảnh {src_image_path} không tồn tại.")
