import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

try:
    water_level = ctrl.Antecedent(np.arange(0, 101, 1), 'WaterLevel')
    valve = ctrl.Consequent(np.arange(0, 101, 1), 'Valve')

    water_level['Low'] = fuzz.trimf(water_level.universe, [0, 15, 30])
    water_level['Okay'] = fuzz.trimf(water_level.universe, [25, 50, 75])
    water_level['High'] = fuzz.trimf(water_level.universe, [70, 85, 100])

    valve['Closed'] = fuzz.trimf(valve.universe, [0, 10, 20])
    valve['PartiallyOpen'] = fuzz.trimf(valve.universe, [40, 50, 60])
    valve['FullyOpen'] = fuzz.trimf(valve.universe, [80, 90, 100])

    rule1 = ctrl.Rule(water_level['Low'], valve['FullyOpen'])
    rule2 = ctrl.Rule(water_level['Okay'], valve['PartiallyOpen'])
    rule3 = ctrl.Rule(water_level['High'], valve['Closed'])

    valve_ctrl_system = ctrl.ControlSystem([rule1, rule2, rule3])
    valve_simulation = ctrl.ControlSystemSimulation(valve_ctrl_system)

    print("Систему нечіткого виведення створено за допомогою scikit-fuzzy.")
    print("Дослідження системи")

    test_levels = [10, 28, 50, 72, 90]

    for level in test_levels:
        try:
            valve_simulation.input['WaterLevel'] = level
            valve_simulation.compute()
            output_value = valve_simulation.output['Valve']
            print(f"При рівні води = {level}, стан клапана = {output_value:.2f}")
        except Exception as e:
             print(f"Помилка обчислення для рівня {level}: {e}")

    print("Дослідження завершено")

except ImportError:
    print("Помилка: Не знайдено бібліотеку scikit-fuzzy або numpy.")
    print("Будь ласка, встановіть їх: pip install numpy scikit-fuzzy")
except Exception as e:
    print(f"Сталася неочікувана помилка: {e}")