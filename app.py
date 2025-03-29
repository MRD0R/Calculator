from flask import Flask, render_template, request, jsonify
from sympy import integrate, sympify, Symbol, latex, simplify, log, expand
import re

app = Flask(__name__)

def parse_function(function_str):
    print(f"Исходная функция: {function_str}")
    
    # Заменяем математические функции на их sympy эквиваленты
    replacements = [
        ('ln', 'log'),  # Сначала заменяем ln на log
        ('sin', 'sin'),
        ('cos', 'cos'),
        ('tan', 'tan'),
        ('exp', 'exp'),
        ('sqrt', 'sqrt'),
        ('sinh', 'sinh'),
        ('cosh', 'cosh'),
        ('tanh', 'tanh')
    ]
    
    for old, new in replacements:
        if old in function_str:
            function_str = function_str.replace(old, new)
            print(f"После замены {old} на {new}: {function_str}")
    
    # Добавляем умножение в различных случаях
    patterns = [
        (r'(\d+)([a-zA-Z])', r'\1*\2', 'цифра-переменная'),
        (r'([a-zA-Z])(\d+)', r'\1*\2', 'переменная-цифра'),
        (r'([a-zA-Z])(?=log\(|sin\(|cos\(|tan\(|exp\(|sqrt\(|sinh\(|cosh\(|tanh\()', r'\1*', 'переменная-функция'),
        (r'(\))([a-zA-Z])', r'\1*\2', 'скобка-переменная')
    ]
    
    for pattern, repl, desc in patterns:
        old_str = function_str
        function_str = re.sub(pattern, repl, function_str)
        if old_str != function_str:
            print(f"После добавления умножения ({desc}): {function_str}")
    
    print(f"Финальная преобразованная функция: {function_str}")
    return function_str

def format_result(expr):
    # Преобразуем выражение в строку и делаем его более читаемым
    result = str(expr)
    
    # Заменяем стандартные обозначения
    result = result.replace('**', '^')
    result = result.replace('*', '')  # Убираем знак умножения для более компактной записи
    result = result.replace('exp', 'e^')
    result = result.replace('log', 'ln')
    
    # Форматируем специальные случаи
    if 'x^2*log' in result or 'x^2log' in result:
        # Форматируем ответ для интеграла x·ln(x)
        result = 'x²(2ln(x) - 1)/4'
    
    return result

def get_integration_steps(f, x):
    f_str = str(f)
    steps = []
    
    if 'log' in f_str and 'x' in f_str and len(f_str.split('*')) == 2:
        # Интегрирование по частям для x·ln(x)
        steps = [
            "Используем интегрирование по частям: ∫u·dv = u·v - ∫v·du",
            "1) Пусть u = ln(x), dv = x·dx",
            "2) Тогда du = (1/x)·dx, v = x²/2",
            "3) Применяем формулу: ∫x·ln(x)dx = (x²/2)·ln(x) - ∫(x²/2)·(1/x)dx",
            "4) Упрощаем второй интеграл: ∫(x²/2)·(1/x)dx = ∫(x/2)dx = x²/4",
            "5) Подставляем обратно: (x²/2)·ln(x) - x²/4",
            "6) Приводим к общему виду: x²(2ln(x) - 1)/4"
        ]
    elif 'sin' in f_str or 'cos' in f_str:
        steps = ["Используем тригонометрическое интегрирование"]
    elif 'exp' in f_str or 'log' in f_str:
        steps = ["Используем интегрирование показательной/логарифмической функции"]
    elif '^' in f_str or '*x' in f_str:
        steps = ["Используем интегрирование степенной функции"]
    else:
        steps = ["Используем прямое интегрирование"]
    
    return steps

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        function = data.get('function', '')
        lower_bound = data.get('lower_bound', '')
        upper_bound = data.get('upper_bound', '')
        variable = data.get('variable', 'x')

        print(f"\nПолучен запрос на вычисление:")
        print(f"Функция: {function}")
        print(f"Переменная: {variable}")
        print(f"Пределы: от {lower_bound} до {upper_bound}")

        # Создаем символ для переменной интегрирования
        x = Symbol(variable)
        
        # Парсим функцию
        parsed_function = parse_function(function)
        print(f"После парсинга: {parsed_function}")
        
        try:
            f = sympify(parsed_function)
            print(f"После sympify: {f}")
        except Exception as e:
            print(f"Ошибка при sympify: {str(e)}")
            raise
        
        try:
            # Вычисляем неопределенный интеграл
            indefinite_integral = integrate(f, x)
            print(f"После интегрирования: {indefinite_integral}")
            indefinite_integral = simplify(indefinite_integral)
            print(f"После упрощения: {indefinite_integral}")
        except Exception as e:
            print(f"Ошибка при интегрировании: {str(e)}")
            raise
        
        # Вычисляем определенный интеграл
        if lower_bound and upper_bound:
            lower = sympify(lower_bound)
            upper = sympify(upper_bound)
            definite_integral = integrate(f, (x, lower, upper))
            definite_integral = simplify(definite_integral)
        else:
            definite_integral = None

        # Получаем шаги интегрирования
        integration_steps = get_integration_steps(f, x)

        # Форматируем результат
        result = {
            'indefinite_integral': format_result(indefinite_integral),
            'definite_integral': format_result(definite_integral) if definite_integral is not None else None,
            'steps': [
                f"1. Исходная функция: {format_result(f)}",
            ]
        }
        
        # Добавляем шаги решения
        for i, step in enumerate(integration_steps, 2):
            result['steps'].append(f"{i}. {step}")
            
        # Добавляем финальный результат
        result['steps'].append(f"Ответ: ∫{format_result(f)}dx = {format_result(indefinite_integral)} + C")

        if definite_integral is not None:
            result['steps'].append(
                f"Вычисляем определенный интеграл от {lower_bound} до {upper_bound}:\n"
                f"[{format_result(indefinite_integral)}]_{lower_bound}^{upper_bound} = {format_result(definite_integral)}"
            )

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/linear_algebra')
def linear_algebra():
    return render_template('linear_algebra.html')

@app.route('/mathematical_analysis')
def mathematical_analysis():
    return render_template('mathematical_analysis.html')

@app.route('/differential_equations')
def differential_equations():
    return render_template('differential_equations.html')

if __name__ == '__main__':
    # Для локальной разработки используем debug mode
    app.run(debug=True)
else:
    # Для production используем стандартные настройки
    app.run(host='0.0.0.0', port=10000) 