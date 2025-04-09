import cv2
import numpy as np
import sys

def add_watermark(main_image_path, watermark_path, output_path, transparency=0.5):
    main_image = cv2.imread(main_image_path)
    watermark = cv2.imread(watermark_path, cv2.IMREAD_UNCHANGED)

    if main_image is None:
        print(f"Помилка: Не вдалося завантажити основне зображення: {main_image_path}")
        return
    if watermark is None:
        print(f"Помилка: Не вдалося завантажити водяний знак: {watermark_path}")
        return

    rgb_watermark = None
    alpha_mask = None

    if len(watermark.shape) == 3 and watermark.shape[2] == 4:
        alpha_channel = watermark[:,:,3]
        rgb_watermark = watermark[:,:,:3]
        alpha_mask = alpha_channel.astype(np.float32) / 255.0
        alpha_mask = cv2.cvtColor(alpha_mask, cv2.COLOR_GRAY2BGR)
    elif len(watermark.shape) == 3 and watermark.shape[2] == 3:
         rgb_watermark = watermark
         alpha_mask = np.ones_like(rgb_watermark, dtype=np.float32) * 1.0
    elif len(watermark.shape) == 2 :
         rgb_watermark = cv2.cvtColor(watermark, cv2.COLOR_GRAY2BGR)
         alpha_mask = np.ones_like(rgb_watermark, dtype=np.float32) * 1.0
    else:
         print(f"Помилка: Непідтримуваний формат водяного знаку: shape={watermark.shape}")
         return

    h_main, w_main = main_image.shape[:2]

    if rgb_watermark is None or rgb_watermark.size == 0:
         print("Помилка: Не вдалося обробити дані водяного знаку.")
         return
    h_wm, w_wm = rgb_watermark.shape[:2]

    max_wm_width = int(w_main * 0.25)
    max_wm_height = int(h_main * 0.25)

    if w_wm > max_wm_width or h_wm > max_wm_height:
        scale = min(max_wm_width / w_wm, max_wm_height / h_wm)
        new_w = int(w_wm * scale)
        new_h = int(h_wm * scale)
        if new_w > 0 and new_h > 0:
             rgb_watermark = cv2.resize(rgb_watermark, (new_w, new_h), interpolation=cv2.INTER_AREA)
             alpha_mask = cv2.resize(alpha_mask, (new_w, new_h), interpolation=cv2.INTER_AREA)
             h_wm, w_wm = new_h, new_w
        else:
             print("Помилка: Водяний знак занадто малий після масштабування.")
             return

    if h_wm > h_main or w_wm > w_main:
        print("Помилка: Водяний знак більший за основне зображення навіть після масштабування.")
        return

    roi_x = w_main - w_wm
    roi_y = h_main - h_wm

    if roi_y < 0 or roi_x < 0:
        print(f"Помилка: Неможливо розмістити водяний знак ({w_wm}x{h_wm}) на зображенні ({w_main}x{h_main}).")
        return

    roi = main_image[roi_y:h_main, roi_x:w_main]

    if roi.shape[:2] != rgb_watermark.shape[:2]:
        print(f"Попередження: Невелике розходження розмірів ROI ({roi.shape[:2]}) та водяного знаку ({rgb_watermark.shape[:2]}). Зміна розміру водяного знаку точно під ROI.")
        if roi.shape[0] > 0 and roi.shape[1] > 0:
            rgb_watermark = cv2.resize(rgb_watermark, (roi.shape[1], roi.shape[0]), interpolation=cv2.INTER_AREA)
            alpha_mask = cv2.resize(alpha_mask, (roi.shape[1], roi.shape[0]), interpolation=cv2.INTER_AREA)
        else:
            print("Помилка: Неприпустимий розмір ROI.")
            return

    effective_alpha_mask = alpha_mask * transparency
    blended_roi = (effective_alpha_mask * rgb_watermark + (1.0 - effective_alpha_mask) * roi).astype(np.uint8)

    main_image[roi_y:h_main, roi_x:w_main] = blended_roi

    try:
        cv2.imwrite(output_path, main_image)
        print(f"Зображення з водяним знаком збережено як: {output_path}")
    except Exception as e:
        print(f"Помилка при збереженні зображення: {e}")
        return

    cv2.imshow('Зображення з водяним знаком', main_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main_img = 'photo.jpg'
    watermark_img = 'watermark.png'
    output_img = 'output_watermarked_image.jpg'
    transparency_level = 0.5

    add_watermark(main_img, watermark_img, output_img, transparency_level)