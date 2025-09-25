from wordcloud import WordCloud
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import os

# Устанавливаем рабочую директорию
os.chdir("C:/Users/Danila/PycharmProjects/Task10")

# Исходный текст
text = (
    "Data science is an interdisciplinary field that uses scientific methods, "
    "processes, algorithms and systems to extract knowledge and insights from "
    "noisy, structured and unstructured data"
)

# Простое облако слов
wordcloud_basic = WordCloud(width=800, height=400, background_color='white').generate(text)

plt.figure(figsize=(10, 5))
plt.imshow(wordcloud_basic, interpolation='bilinear')
plt.axis('off')
plt.title('Простое облако слов')
plt.show()

# Облако слов в форме сердца
heart_mask = np.array(Image.open("heart.png"))
wordcloud_heart = WordCloud(background_color="white", mask=heart_mask, contour_color='red', contour_width=1).generate(text)

plt.figure(figsize=(8, 8))
plt.imshow(wordcloud_heart, interpolation='bilinear')
plt.axis('off')
plt.title('Облако в форме сердца')
plt.show()

# Облако слов в форме звезды
star_mask = np.array(Image.open("star.png"))
wordcloud_star = WordCloud(background_color="white", mask=star_mask, contour_color='blue', contour_width=1).generate(text)

plt.figure(figsize=(8, 8))
plt.imshow(wordcloud_star, interpolation='bilinear')
plt.axis('off')
plt.title('Облако в форме звезды')
plt.show()
