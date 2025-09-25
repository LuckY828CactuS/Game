import tensorflow as tf
import tensorflow_datasets as tfds
from IPython.display import clear_output
import matplotlib.pyplot as plt

# Загрузка датасета
dataset, info = tfds.load('oxford_iiit_pet:4.0.0', with_info=True)


def load_image(x):
    # Ресайз и нормализация изображения
    input_image = tf.image.resize(x['image'], (128, 128)) / 255.0

    # Ресайз маски с интерполяцией 'nearest' (чтобы не было дробных значений)
    input_mask = tf.image.resize(
        x['segmentation_mask'], (128, 128), method='nearest'
    )
    # Если классы начинаются с 1, сдвигаем на 1
    input_mask = input_mask - 1

    return input_image, input_mask


# Применение обработки
train_images = dataset['train'].map(load_image, num_parallel_calls=tf.data.AUTOTUNE)
test_images = dataset['test'].map(load_image, num_parallel_calls=tf.data.AUTOTUNE)

# Проверка первого элемента
sample_image, sample_mask = next(iter(train_images))
print("Image shape:", sample_image.shape)  # (128, 128, 3)
print("Mask shape:", sample_mask.shape)  # (128, 128, 1)
print("Mask unique values:", tf.unique(tf.reshape(sample_mask, [-1])))  # Проверка классов