"""
This script calculates mortgage payments based on monthly payments or mortgage time

Этот скрипт считает платежи по ипотеке в зависимости от ежемесячных платежей или срока ипотеки

Date/time: 18.06.2022 22:45
Author: Maksim Makarov (MisterMaks97@mail.ru)
"""


import logging
import traceback
import time
from typing import Union, Tuple, List, Dict
from dataclasses import dataclass, asdict
import csv


logging.basicConfig(
    format=u'%(levelname)-8s [%(asctime)s] %(message)s',
    level=logging.INFO,
    handlers=[logging.FileHandler('mortgage_calculator.log')]
)

logger = logging.getLogger(__name__)


FILENAME = f'Расчет платежей по ипотеке.csv'
PATH = f'./{FILENAME}'
MODES = {
    1: 'расчет срока ипотеки в зависимости от ежемесячных платежей',
    2: 'расчет ежемесячных платежей по ипотеке в зависимости от срока',
    3: 'расчет банка'
}


@dataclass
class UserInputData:
    mode: int
    mortgage_amount: int
    mortgage_percents_1: float
    mortgage_percents_2: float
    mortgage_monthly_payments: float
    mortgage_months_period: int

    def check_data(self):
        if self.mode not in (1, 2, 3):
            logger.error(f'Bad mode. mode: {self.mode} not in (1, 2)')
            print('Ошибка. Данного режима нет')
            return False
        if self.mortgage_amount < 0:
            logger.error(f'Bad mortgage_amount. mortgage_amount: {self.mortgage_amount} < 0')
            print('Ошибка. Размер ипотеки < 0')
            return False
        if self.mortgage_percents_1 < 0:
            logger.error(f'Bad mortgage_percents_1. mortgage_percents_1: {self.mortgage_percents_1} < 0')
            print('Ошибка. Процентная ставка за 1-ый год < 0')
            return False
        if self.mortgage_percents_2 < 0:
            logger.error(f'Bad mortgage_percents_2. mortgage_percents_2: {self.mortgage_percents_2} < 0')
            print('Ошибка. Процентная ставка со 2-ого года < 0')
            return False
        if self.mortgage_monthly_payments < 0:
            logger.error(f'Bad mortgage_monthly_payments. mortgage_monthly_payments: {self.mortgage_monthly_payments} < 0')
            print('Ошибка. Ежемесячный платеж < 0')
            return False
        if self.mortgage_months_period < 0:
            logger.error(f'Bad mortgage_months_period. mortgage_months_period: {self.mortgage_months_period} < 0')
            print('Ошибка. Период ипотеки < 0')
            return False
        return True


@dataclass
class MortgageMonthlyPaymentData:
    month: int
    mortgage_debt: float
    mortgage_percents_val: float
    mortgage_percents: float
    payment_debt_val: float
    mortgage_monthly_payments: float

    def get_str(self):
        return f'Месяц: {self.month}. ' \
               f'Остаток ссудной задолженности: {round(self.mortgage_debt, 3)}. ' \
               f'Проценты: {round(self.mortgage_percents_val, 3)} ({self.mortgage_percents} %). ' \
               f'Ссудная задолженность: {round(self.payment_debt_val, 3)}. ' \
               f'Плановый платеж: {round(self.mortgage_monthly_payments, 3)}.'


def save_in_csv(
        path: str,
        user_input_data_json: Dict[str, Union[int, float, str]],
        mortgage_monthly_payments: float,
        mortgage_months_period: int,
        mortgage_monthly_payments_data_json: List[Dict[str, Union[int, float]]],
        mortgage_monthly_payments_2: Union[float, None] = None
):
    logger.info('Save in csv file')
    with open(path, 'w') as f:
        writer = csv.DictWriter(f, fieldnames=user_input_data_json.keys())
        writer.writerow({
            'mode': 'Режим',
            'mortgage_amount': 'Сумма ипотеки',
            'mortgage_percents_1': 'Процентная ставка в 1 год',
            'mortgage_percents_2': 'Процентная ставка со 2-го года',
            'mortgage_monthly_payments': 'Ежемесячный платеж',
            'mortgage_months_period': 'Срок ипотеки (в месяцах)',
        })
        for key, value in user_input_data_json.items():
            if key == 'mode':
                user_input_data_json[key] = f'{value} ({MODES[value]})'
                continue
            user_input_data_json[key] = round(value, 3)
        writer.writerow(user_input_data_json)

        writer = csv.writer(f)
        if not mortgage_monthly_payments_2:
            writer.writerow(['Ежемесячный платеж', 'Срок ипотеки (в месяцах)'])
            writer.writerow([round(mortgage_monthly_payments, 3), f'{mortgage_months_period} месяц/месяцев ({mortgage_months_period // 12} год/лет и {mortgage_months_period % 12} месяц/месяцев)'])
        else:
            writer.writerow(['Ежемесячный платеж в 1-ый год', 'Ежемесячный платеж со 2-ого года', 'Срок ипотеки (в месяцах)'])
            writer.writerow([round(mortgage_monthly_payments, 3), round(mortgage_monthly_payments_2, 3), f'{mortgage_months_period} месяц/месяцев ({mortgage_months_period // 12} год/лет и {mortgage_months_period % 12} месяц/месяцев)'])

        writer = csv.DictWriter(f, fieldnames=mortgage_monthly_payments_data_json[0].keys())
        writer.writerow({
            'month': 'Месяц',
            'mortgage_debt': 'Остаток ссудной задолженности',
            'mortgage_percents_val': 'Проценты',
            'mortgage_percents': 'Процентная ставка',
            'payment_debt_val': 'Ссудная задолженность',
            'mortgage_monthly_payments': 'Ежемесячный платеж'
        })
        for mortgage_monthly_payment_data_json in mortgage_monthly_payments_data_json:
            for key, value in mortgage_monthly_payment_data_json.items():
                try:
                    mortgage_monthly_payment_data_json[key] = round(value, 3)
                except ValueError:
                    logger.critical(f'Failed save_in_csv() in round(). Error: \n{traceback.format_exc()}')
            writer.writerow(mortgage_monthly_payment_data_json)


def get_user_input_data() -> Union[UserInputData, None]:
    logger.info('Get user input data')
    try:
        mode = int(input(
            'Выберете режим 1 - (расчет срока ипотеки в зависимости от ежемесячных платежей) или '
            '2 - (расчет ежемесячных платежей по ипотеке в зависимости от срока) или '
            '3 - (расчет как в банке): '
        ))
        mortgage_amount = int(input('Введите сумму ипотеки: '))
        mortgage_percents_1 = float(input('Введите процент по ипотеке в первый год (только число, разделитель точка): '))
        mortgage_percents_2 = float(input('Введите процент по ипотеке со второго года (только число, разделитель точка): '))
        if mode == 1:
            mortgage_monthly_payments = float(input('Введите ежемесячные платежи по ипотеке: '))
            return UserInputData(mode, mortgage_amount, mortgage_percents_1, mortgage_percents_2, mortgage_monthly_payments, 0)
        elif mode in (2, 3):
            mortgage_month_period = int(input('Введите период ипотеки (кол-во месяцев): '))
            return UserInputData(mode, mortgage_amount, mortgage_percents_1, mortgage_percents_2, 0, mortgage_month_period)
        else:
            logger.error(f'Bad mode')
            print('Данного режима нет')
            return
    except ValueError:
        logger.error(f'Failed get_user_input_data(). Bad user input data. User input data is not converted to an int type. Error: \n{traceback.format_exc()}')
        print('Плохой ввод. Пользовательские данные не числа.')
        return


def mortgage_time_calculation(
        mortgage_amount: int,
        mortgage_percents_1: float,
        mortgage_percents_2: float,
        mortgage_monthly_payments: float,
) -> Tuple[List[MortgageMonthlyPaymentData], int]:
    logger.info('Calculation mortgage time')
    print('Расчет срока ипотеки в зависимости от ежемесячных платежей')
    count_months = 0
    mortgage_monthly_payments_data = []
    while mortgage_amount:
        mortgage_amount_previous = mortgage_amount
        count_months += 1
        if count_months <= 12:
            mortgage_percents = mortgage_percents_1
        else:
            mortgage_percents = mortgage_percents_2
        mortgage_percents_val = (mortgage_amount*(mortgage_percents/100))/12
        mortgage_debt = mortgage_amount
        mortgage_amount += mortgage_percents_val
        if mortgage_amount < mortgage_monthly_payments:
            mortgage_monthly_payments = mortgage_amount
        payment_debt_val = mortgage_monthly_payments - mortgage_percents_val
        mortgage_amount -= mortgage_monthly_payments
        if mortgage_amount > mortgage_amount_previous:
            logger.error('With such user inputs mortgage will rise')
            print('При таких параметрах ипотека будет расти')
            break
        mortgage_monthly_payment_data = MortgageMonthlyPaymentData(count_months, mortgage_debt, mortgage_percents_val, mortgage_percents, payment_debt_val, mortgage_monthly_payments)
        mortgage_monthly_payments_data.append(mortgage_monthly_payment_data)
        print(mortgage_monthly_payment_data.get_str())
    print(f'Кол-во месяцев: {count_months} ({count_months//12} года/лет и {count_months % 12} месяц/месяцев)')
    return mortgage_monthly_payments_data, count_months


def mortgage_payment_calculation(mortgage_amount: int, mortgage_percents_1: float, mortgage_percents_2: float, mortgage_month_period: int) -> Union[float, None]:
    logger.info('Calculation mortgage monthly payments')
    print('Расчет ежемесячных платежей по ипотеке в зависимости от срока')
    try:
        if mortgage_month_period <= 12:
            mortgage_amount_with_percents_val = mortgage_amount * ((1 + mortgage_percents_1 / (100 * 12)) ** mortgage_month_period)
        else:
            mortgage_amount_with_percents_val = mortgage_amount * ((1 + mortgage_percents_1 / (100 * 12)) ** 12) * ((1 + mortgage_percents_2 / (100 * 12)) ** (mortgage_month_period - 12))
        divider = 0
        count_months = 0
        while count_months < mortgage_month_period:
            count_months += 1
            if count_months <= 12:
                divider += (1 + mortgage_percents_1 / (100 * 12)) ** (mortgage_month_period - count_months)
            else:
                divider += (1 + mortgage_percents_2 / (100 * 12)) ** (mortgage_month_period - count_months)
        mortgage_monthly_payments = mortgage_amount_with_percents_val / divider
        print(f'Ежемесячный платеж: {round(mortgage_monthly_payments, 3)}')
        return mortgage_monthly_payments
    except ZeroDivisionError:
        logger.error(f'Failed mortgage_payment_calculation(). ZeroDivisionError. Error: \n{traceback.format_exc()}')
        print('Ошибка. Произошло деление на 0')
        return


def mortgage_bank_calculation(mortgage_amount: int, mortgage_percents_1: float, mortgage_percents_2: float, mortgage_month_period: int) -> Tuple[List[MortgageMonthlyPaymentData], int, float, float]:
    logger.info('Calculation mortgage as bank')
    print('Расчет ипотеки (как банк)')
    monthly_rate = (mortgage_percents_1 / (12 * 100))
    total_rate = (1 + monthly_rate) ** mortgage_month_period
    mortgage_monthly_payments = mortgage_amount * monthly_rate * total_rate / (total_rate - 1)
    mortgage_monthly_payments_1 = mortgage_monthly_payments
    mortgage_monthly_payments_2 = 0
    count_months = 0
    mortgage_monthly_payments_data = []
    while mortgage_amount:
        mortgage_amount_previous = mortgage_amount
        count_months += 1
        if count_months <= 12:
            mortgage_percents = mortgage_percents_1
        else:
            mortgage_percents = mortgage_percents_2
            if count_months == 13:
                monthly_rate = (mortgage_percents_2 / (12 * 100))
                total_rate = (1 + monthly_rate) ** (mortgage_month_period - 12)
                mortgage_monthly_payments = mortgage_amount * monthly_rate * total_rate / (total_rate - 1)
                mortgage_monthly_payments_2 = mortgage_monthly_payments
        mortgage_percents_val = (mortgage_amount * (mortgage_percents / 100)) / 12
        mortgage_debt = mortgage_amount
        mortgage_amount += mortgage_percents_val
        if mortgage_amount < mortgage_monthly_payments:
            mortgage_monthly_payments = mortgage_amount
        payment_debt_val = mortgage_monthly_payments - mortgage_percents_val
        mortgage_amount -= mortgage_monthly_payments
        if mortgage_amount > mortgage_amount_previous:
            logger.error('With such user inputs mortgage will rise')
            print('При таких параметрах ипотека будет расти')
            break
        mortgage_monthly_payment_data = MortgageMonthlyPaymentData(count_months, mortgage_debt, mortgage_percents_val, mortgage_percents, payment_debt_val, mortgage_monthly_payments)
        mortgage_monthly_payments_data.append(mortgage_monthly_payment_data)
        print(mortgage_monthly_payment_data.get_str())
    print(f'Кол-во месяцев: {count_months} ({count_months // 12} года/лет и {count_months % 12} месяц/месяцев)')
    return mortgage_monthly_payments_data, count_months, mortgage_monthly_payments_1, mortgage_monthly_payments_2


def main():
    user_input_data = get_user_input_data()
    if not user_input_data:
        return
    if not user_input_data.check_data():
        return
    if user_input_data.mode == 1:
        mortgage_monthly_payments_data, count_months = mortgage_time_calculation(
            user_input_data.mortgage_amount,
            user_input_data.mortgage_percents_1,
            user_input_data.mortgage_percents_2,
            user_input_data.mortgage_monthly_payments)
        user_input_data.mortgage_months_period = count_months
        mortgage_monthly_payments_data_json = [asdict(mortgage_monthly_payment_data) for mortgage_monthly_payment_data in mortgage_monthly_payments_data]
        if not mortgage_monthly_payments_data_json:
            logger.error('No data for saving')
            print('Ошибка. Нет данных для сохранения. Проверьте введенные данные.')
            return
        save_in_csv(PATH, asdict(user_input_data), user_input_data.mortgage_monthly_payments, count_months, mortgage_monthly_payments_data_json)
    if user_input_data.mode == 2:
        mortgage_monthly_payments = mortgage_payment_calculation(
            user_input_data.mortgage_amount,
            user_input_data.mortgage_percents_1,
            user_input_data.mortgage_percents_2,
            user_input_data.mortgage_months_period
        )
        if not mortgage_monthly_payments:
            return
        user_input_data.mortgage_monthly_payments = mortgage_monthly_payments
        mortgage_monthly_payments_data, count_months = mortgage_time_calculation(
            user_input_data.mortgage_amount,
            user_input_data.mortgage_percents_1,
            user_input_data.mortgage_percents_2,
            user_input_data.mortgage_monthly_payments)
        user_input_data.mortgage_months_period = count_months
        mortgage_monthly_payments_data_json = [asdict(mortgage_monthly_payment_data) for mortgage_monthly_payment_data in mortgage_monthly_payments_data]
        if not mortgage_monthly_payments_data_json:
            logger.error('No data for saving')
            print('Ошибка. Нет данных для сохранения. Проверьте введенные данные.')
            return
        save_in_csv(PATH, asdict(user_input_data), user_input_data.mortgage_monthly_payments, count_months, mortgage_monthly_payments_data_json)
    if user_input_data.mode == 3:
        mortgage_monthly_payments_data, count_months, mortgage_monthly_payments_1, mortgage_monthly_payments_2 = mortgage_bank_calculation(
            user_input_data.mortgage_amount,
            user_input_data.mortgage_percents_1,
            user_input_data.mortgage_percents_2,
            user_input_data.mortgage_months_period
        )
        user_input_data.mortgage_months_period = count_months
        mortgage_monthly_payments_data_json = [asdict(mortgage_monthly_payment_data) for mortgage_monthly_payment_data in mortgage_monthly_payments_data]
        if not mortgage_monthly_payments_data_json:
            logger.error('No data for saving')
            print('Ошибка. Нет данных для сохранения. Проверьте введенные данные.')
            return
        save_in_csv(PATH, asdict(user_input_data), mortgage_monthly_payments_1, count_months, mortgage_monthly_payments_data_json, mortgage_monthly_payments_2)
    return


if __name__ == '__main__':
    logger.info('Script running...')
    time_start = time.time()
    try:
        main()
    except Exception:
        logger.critical(f'Failed main(). Error: \n{traceback.format_exc()}')
        print("Что-то пошло не так")
    logger.info(f'Script finished. Time work: {int(time.time() - time_start)} seconds')
