import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.datasets import mnist
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.metrics import confusion_matrix, classification_report
import random

def run_mnist_cnn_pipeline():

    print("Крок 1: Завантаження та підготовка даних MNIST")
    (x_train, y_train), (x_test, y_test) = mnist.load_data()

    x_train = x_train.astype("float32") / 255.0
    x_test = x_test.astype("float32") / 255.0

    x_train = np.expand_dims(x_train, -1)
    x_test = np.expand_dims(x_test, -1)

    num_classes = 10
    y_train_cat = to_categorical(y_train, num_classes)
    y_test_cat = to_categorical(y_test, num_classes)

    print(f"Розмір тренувальних даних: {x_train.shape}")
    print(f"Розмір тестових даних: {x_test.shape}")
    print("Нормалізація та перетворення міток завершено.")

    print("\nКрок 2: Побудова архітектури CNN")
    input_shape = (28, 28, 1)

    def build_model(input_shape, num_classes, filters1=32, filters2=64, dense_units=128, dropout1=0.25, dropout2=0.5):
        model = Sequential([
            keras.Input(shape=input_shape),
            layers.Conv2D(filters1, kernel_size=(3, 3), activation="relu"),
            layers.MaxPooling2D(pool_size=(2, 2)),
            layers.Conv2D(filters2, kernel_size=(3, 3), activation="relu"),
            layers.MaxPooling2D(pool_size=(2, 2)),
            layers.Dropout(dropout1),
            layers.Flatten(),
            layers.Dense(dense_units, activation="relu"),
            layers.Dropout(dropout2),
            layers.Dense(num_classes, activation="softmax"),
        ])
        return model

    model = build_model(input_shape, num_classes)
    model.summary()
    print("Модель CNN створено.")

    print("\nКрок 3: Навчання моделі")
    batch_size = 32
    epochs = 10

    model.compile(loss="categorical_crossentropy", optimizer="adam", metrics=["accuracy"])

    print("Початок навчання...")
    history = model.fit(x_train, y_train_cat,
                        batch_size=batch_size,
                        epochs=epochs,
                        validation_split=0.2)
    print("Навчання завершено.")

    print("\nКрок 4: Візуалізація результатів навчання")

    def plot_history(history):
        acc = history.history['accuracy']
        val_acc = history.history['val_accuracy']
        loss = history.history['loss']
        val_loss = history.history['val_loss']
        epochs_range = range(1, len(acc) + 1)

        plt.figure(figsize=(12, 5))

        plt.subplot(1, 2, 1)
        plt.plot(epochs_range, acc, 'bo-', label='Точність на тренуванні')
        plt.plot(epochs_range, val_acc, 'ro-', label='Точність на валідації')
        plt.title('Точність моделі')
        plt.xlabel('Епохи')
        plt.ylabel('Точність')
        plt.legend()

        plt.subplot(1, 2, 2)
        plt.plot(epochs_range, loss, 'bo-', label='Втрати на тренуванні')
        plt.plot(epochs_range, val_loss, 'ro-', label='Втрати на валідації')
        plt.title('Втрати моделі')
        plt.xlabel('Епохи')
        plt.ylabel('Втрати')
        plt.legend()

        plt.tight_layout()
        plt.show()

    plot_history(history)
    print("Графіки точності та втрат відображено.")

    print("\nКрок 5: Оцінка моделі на тестових даних")
    score = model.evaluate(x_test, y_test_cat, verbose=0)
    print(f"Тестові втрати: {score[0]:.4f}")
    print(f"Тестова точність: {score[1]:.4f}")

    y_pred = model.predict(x_test)
    y_pred_classes = np.argmax(y_pred, axis=1)
    y_true = np.argmax(y_test_cat, axis=1)

    conf_matrix = confusion_matrix(y_true, y_pred_classes)

    plt.figure(figsize=(8, 6))
    sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues', xticklabels=range(num_classes), yticklabels=range(num_classes))
    plt.xlabel('Передбачений клас')
    plt.ylabel('Справжній клас')
    plt.title('Матриця плутанини')
    plt.show()

    print("\nЗвіт по класифікації:")
    print(classification_report(y_true, y_pred_classes, target_names=[str(i) for i in range(num_classes)]))
    print("Оцінка на тестових даних та матриця плутанини відображені.")

    print("\nКрок 6: Прогноз на тестових даних")

    def predict_digit(image_data, model_instance):
        if image_data.shape != (28, 28, 1):
             if image_data.shape == (28,28):
                 image_data = np.expand_dims(image_data, -1)
             else:
                 print("Неправильна форма вхідного зображення для передбачення.")
                 return None

        image_batch = np.expand_dims(image_data, axis=0)
        prediction = model_instance.predict(image_batch)
        predicted_class = np.argmax(prediction, axis=1)
        return predicted_class[0]

    plt.figure(figsize=(10, 5))
    for i in range(10):
        idx = random.randint(0, x_test.shape[0] - 1)
        image = x_test[idx]
        true_label = y_test[idx]
        predicted_label = predict_digit(image, model)

        plt.subplot(2, 5, i + 1)
        plt.imshow(image.squeeze(), cmap='gray')
        plt.title(f"True: {true_label}\nPred: {predicted_label}")
        plt.axis('off')
    plt.tight_layout()
    plt.show()
    print("Приклади передбачень на тестових зображеннях відображено.")


    print("\nКрок 7: Покращення моделі (Аугментація даних)")
    datagen = ImageDataGenerator(
        rotation_range=10,
        width_shift_range=0.1,
        height_shift_range=0.1,
        zoom_range=0.1
    )

    model_augmented = build_model(input_shape, num_classes)
    model_augmented.compile(loss="categorical_crossentropy", optimizer="adam", metrics=["accuracy"])

    print("Початок навчання з аугментацією...")

    from sklearn.model_selection import train_test_split
    x_train_aug_base, x_val_aug, y_train_aug_base, y_val_aug = train_test_split(
        x_train, y_train_cat, test_size=0.2, random_state=42
    )

    history_augmented = model_augmented.fit(
        datagen.flow(x_train_aug_base, y_train_aug_base, batch_size=batch_size),
        epochs=epochs,
        validation_data=(x_val_aug, y_val_aug),
        steps_per_epoch=len(x_train_aug_base) // batch_size
    )
    print("Навчання з аугментацією завершено.")

    print("Візуалізація результатів навчання з аугментацією:")
    plot_history(history_augmented)

    print("Оцінка моделі з аугментацією на тестових даних:")
    score_augmented = model_augmented.evaluate(x_test, y_test_cat, verbose=0)
    print(f"Тестові втрати (аугментація): {score_augmented[0]:.4f}")
    print(f"Тестова точність (аугментація): {score_augmented[1]:.4f}")
    print(f"Порівняння точності: Базова={score[1]:.4f}, Аугментована={score_augmented[1]:.4f}")

    print("\nКрок 8: Експерименти з архітектурою")
    print("Приклад: Збільшення кількості фільтрів.")
    model_more_filters = build_model(input_shape, num_classes, filters1=64, filters2=128)
    model_more_filters.compile(loss="categorical_crossentropy", optimizer="adam", metrics=["accuracy"])
    print("Створено модель зі збільшеною кількістю фільтрів.")
    print("Для порівняння потрібно провести повне навчання цієї моделі (пропускається для швидкості).")
    print("Запустіть model_more_filters.fit(...) та model_more_filters.evaluate(...) для отримання результатів.")
    print("Наприклад, точність може зрости, але ризик перенавчання та час навчання також збільшаться.")

    print("\nКрок 9: Збереження та завантаження моделі")
    model_filename = 'mnist_cnn_model.keras'
    model_augmented.save(model_filename)
    print(f"Модель збережено у файл: {model_filename}")

    loaded_model = tf.keras.models.load_model(model_filename)
    print("Модель завантажено.")

    print("Перевірка завантаженої моделі на тестових даних:")
    score_loaded = loaded_model.evaluate(x_test, y_test_cat, verbose=0)
    print(f"Тестові втрати (завантажена): {score_loaded[0]:.4f}")
    print(f"Тестова точність (завантажена): {score_loaded[1]:.4f}")

    print("Приклад передбачення завантаженою моделлю:")
    idx = random.randint(0, x_test.shape[0] - 1)
    image = x_test[idx]
    true_label = y_test[idx]
    predicted_label = predict_digit(image, loaded_model)
    print(f"Випадкове зображення: Справжня мітка={true_label}, Передбачена мітка={predicted_label}")
    plt.imshow(image.squeeze(), cmap='gray')
    plt.title(f"Завантажена модель\nTrue: {true_label}, Pred: {predicted_label}")
    plt.axis('off')
    plt.show()

    print("\nЗавдання виконано")

if __name__ == '__main__':
    run_mnist_cnn_pipeline()