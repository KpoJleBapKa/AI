import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score

X = np.array([
    [0, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 0, 1, 1],
    [0, 1, 0, 0], [0, 1, 0, 1], [0, 1, 1, 0], [0, 1, 1, 1],
    [1, 0, 0, 0], [1, 0, 0, 1], [1, 0, 1, 0], [1, 0, 1, 1],
    [1, 1, 0, 0], [1, 1, 0, 1], [1, 1, 1, 0], [1, 1, 1, 1]
])

Y = np.array([0, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1])

mlp = MLPClassifier(hidden_layer_sizes=(2,),
                    activation='logistic',
                    solver='adam',
                    max_iter=2000,
                    random_state=42,
                    learning_rate_init=0.01)

print("Навчання нейронної мережі...")
mlp.fit(X, Y)
print("Навчання завершено.")

print("\nВагові коефіцієнти:")
print("Ваги між вхідним та прихованим шаром:")
print(mlp.coefs_[0])
print("\nЗсуви (bias) для прихованого шару:")
print(mlp.intercepts_[0])
print("\nВаги між прихованим та вихідним шаром:")
print(mlp.coefs_[1])
print("\nЗсув (bias) для вихідного шару:")
print(mlp.intercepts_[1])

print("\nТестування мережі:")
Y_pred = mlp.predict(X)

print("Вхідні дані (X):")
print(X)
print("\nПередбачені мережею значення (Y_pred):")
print(Y_pred)
print("\nОчікувані значення (Y_actual):")
print(Y)

accuracy = accuracy_score(Y, Y_pred)
print("\nАналіз якості навчання:")
print(f"Точність моделі на навчальних (тестових) даних: {accuracy * 100:.2f}%")

if accuracy == 1.0:
    print("Мережа успішно навчилася відтворювати логічну функцію.")
else:
    print("Мережа не змогла ідеально відтворити функцію.")