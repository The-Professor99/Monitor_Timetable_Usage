import datetime
from collections import defaultdict
import joblib
import statistics
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
from typing import Literal
from datetime import datetime
import sys

def decorate_print(func):
    def inner(*args,  silent=False, **kwargs):
        if not silent:
            print("\n", "=" * 20) 
            func(*args, **kwargs)
            print( "=" * 20)
    return inner 
custom_print = decorate_print(print)

class TimetableUsed:
        """
    Represents a class for managing daily timetable expectations and owed tasks.

    Attributes:
        all_generated_day_expectations (list): A list to store generated daily expectations.
        day_achievements (list): A list to store daily achievements.
        owed (list): A list to track owed tasks.
        tasks_done (list): A list to store completed tasks.
        main_generated_day_expectations (list): A list to store primary daily expectations.
        owed_today (dict): A dictionary to track tasks owed for the current day.
        dates (list): A list of all the days when tasks were done.
    """
        def __init__(self):
            """
            Initializes a new instance of the TimetableUsed class.
            """
            self.all_generated_day_expectations = []
            self.day_achievements = []
            self.owed = []
            self.tasks_done = []
            self.main_generated_day_expectations = []
            self.owed_today = defaultdict(self.return_0)
            self.dates = []

        def generate_day_expectations(self, date, expected, silent=False):
            """
            Generates daily expectations based on the date and expected tasks.

            Args:
                date (str): Eg. Monday 25th September 2023.
                expected (dict): A dictionary of expected tasks.

            """
            day = date.split(" ")[0]

            # Make a copy of the expected tasks for the day
            day_expectations = defaultdict(self.return_0, expected[day])
            custom_print("Todays Expectations:", day_expectations, silent=silent)
            custom_print("When there's time, owes:", self.owed[-1] if self.owed else {},  silent=silent)

            # Make a copy of the expected tasks for the day
            for owed in self.owed[-1].keys() if self.owed else []:
                day_expectations[owed] += self.owed[-1][owed]
                   

            # Store the generated expectations
            if len(self.dates) and date in self.dates:
                raise Exception("Possible Duplicate Entry, please ensure you are \
                not entering the same data twice")
            self.dates.append(date)
            self.main_generated_day_expectations.append(expected[day])
            self.all_generated_day_expectations.append(day_expectations)
            

        def add_tasks_done(self, tasks_done):
            """
            Args:
                tasks_done (dict): A dictionary of completed tasks for the day with number of hours. Eg. {"Coding": 2, "Cooking": 4}

            """
            # Store the completed tasks
            self.day_achievements.append(defaultdict(self.return_0, tasks_done))

        def retrieve_achievements_expectations_and_owed(self, copy_owed=False):
            """
            Retrieve the daily achievements and main expectations

            """
            day_achievements = self.day_achievements[-1].copy()
            main_generated_day_expectation = self.main_generated_day_expectations[-1]
            if copy_owed:
                owed = self.owed[-1].copy() if self.owed else defaultdict(self.return_0)
            else:
                owed = self.owed[-1] if self.owed else defaultdict(self.return_0)
            return day_achievements, main_generated_day_expectation, owed

        def handle_day_only_expectation(self):
            """
            Handles tasks that are expected to be done for the day.

            """
            day_achievements, main_generated_day_expectation, owed = self.retrieve_achievements_expectations_and_owed(copy_owed=True)
            self.owed_today = defaultdict(self.return_0)

            # Calculate owed tasks for the day
            for task, expected in main_generated_day_expectation.items():
                achieved = day_achievements[task]
                difference = expected - achieved

                if difference > 0:
                    owed[task] += round(difference, 2)
                    self.owed_today[task] += difference

            # Store the updated owed tasks
            self.owed.append(owed)

        def handle_exceeded_time(self):
            """
            Handles tasks that exceeded the expected time.

            """
            day_achievements, main_generated_day_expectation, owed = self.retrieve_achievements_expectations_and_owed()

            # Calculate owed tasks for tasks that exceeded time
            for task, achieved in day_achievements.items():
                if task in main_generated_day_expectation:
                    expected = main_generated_day_expectation[task]
                    difference = achieved - expected

                    if difference > 0:
                        owed[task] -= round(difference, 2)

                    # Filter out owed tasks with zero values
                    owed_today = {key: value for key, value in self.owed_today.items() if value != 0}

                    #
                    self.calculate_task_splits(task, owed_today, owed, difference)

        def handle_use_outside_time(self):
            """
            Handles tasks used outside the expected time.

            """
            day_achievements, main_generated_day_expectation, owed = self.retrieve_achievements_expectations_and_owed()
            owed = self.owed[-1] if self.owed else defaultdict(self.return_0)

            # Calculate owed tasks for tasks used outside time
            for task, achieved in day_achievements.items():
                if task not in main_generated_day_expectation:
                    expected = 0
                    difference = achieved - expected
                    owed[task] -= round(difference, 2)

                    # Filter out owed tasks with zero values
                    owed_today = {key: value for key, value in self.owed_today.items() if value != 0}
                    self.calculate_task_splits(task, owed_today, owed, difference)

        def calculate_owed(self):
            self.handle_day_only_expectation()
            self.handle_exceeded_time()
            self.handle_use_outside_time()
            
        def calculate_task_splits(self, task, owed_today, owed, difference):
            """
            Args:
                task (str): The task for which the split is calculated.
                owed_today (dict): A dictionary of tasks owed for the current day.
                owed (dict): A dictionary of owed tasks.
                difference (float): The difference between expected and achieved for the task.
            """
            if difference < 0:
                return

            owed_today_copy = {key: value for key, value in owed_today.items() if value != 0}
            true_difference =  round(difference, 2)

            #
            for name, value_owed in owed_today_copy.items():
                split = self.compute_split(name, value_owed, owed_today_copy, difference)
                true_difference -= split
                self.owed_today[name] -= split
                owed[task + "To" + name] -= split

            #
            if true_difference > 0:
                owed[task + "ToFreeTime"] -= true_difference
        
        #getters
        def get_total_daily_achievements(self):
            return pd.DataFrame(self.day_achievements).sum(axis=1).rename("Hours Worked")
        def get_all_owings(self):
            return self.owed
        def get_achievements_and_expectations(self):
            return self.day_achievements, self.main_generated_day_expectations
        def get_dates(self):
            return self.dates
                
        @staticmethod
        def compute_split(name, value_owed, total_owed, total_value):
            """
            Computes the split amount for a task based on owed values and total value.

            Args:
                name (str): The name of the category.
                value_owed (float): The amount owed for the category.
                total_owed (dict): A dictionary of total owed values.
                total_value (float): The total value to be split.

            Returns:
                float: The computed split amount.

            """
            split = (value_owed / sum(total_owed.values())) * total_value
            return  round(value_owed, 2) if split > value_owed else round(split, 2)

        @staticmethod
        def return_0():
            return 0

def calculate_all_data(timetable, date, tasks_done, expected=None, silent=False):
    timetable.generate_day_expectations(date, expected, silent=silent)
    timetable.add_tasks_done(tasks_done)
    custom_print(f"{date} Achievements", dict(timetable.day_achievements[-1]))
    timetable.calculate_owed()
    custom_print("Owes: ", timetable.owed[-1], silent=silent)
    return timetable
    
def run_setup(expected, date, tasks_done, silent=False, timetable_path="timetable_used1.pkl"):
    try:
        timetable_used = joblib.load(timetable_path)
    except FileNotFoundError:
        timetable_used = TimetableUsed()    
    calculate_all_data(timetable_used, date, tasks_done, expected, silent=silent)
    print("Please ensure everything from above calculations are right before saving.")
    save = input("Do you want to save this entry? (y/N)")
    if save == "y":
        joblib.dump(timetable_used, timetable_path) 
    return timetable_used

def sort_dict(dict_obj):
    sorted_dict = {}
    for key in sorted(dict_obj):
        sorted_dict[key] = dict_obj[key]
    return sorted_dict

def plot_mean_median(series: pd.Series, num_days: int=7, kind: Literal["line", "hist", "box", "bar"] ="bar",  median=False) -> None:
    """
    num_days: span of days used in calculating the median
    kind: kind of plot to plot. passed to matplotlib.pyplot.plot.
    """
    if len(series) < num_days:
        custom_print(f"Nothing to plot, please ensure data in series is up to specified {num_days}days")
        return
    if median:
        series.rolling(window=num_days).median().dropna().plot(kind=kind, title="Average number of hrs(median) plot")
    else:
        series.rolling(window=num_days).mean().dropna().plot(kind=kind, title="Average number of hrs(mean) plot")
    
def hours_worked_plot(series: pd.Series, min_hrs: float=8, opt_hrs: float=10):
    df = series.to_frame()
    df["Minimum Hours Required per day"] = min_hrs
    df["Optimal Hours Required per day"] = opt_hrs
    ax = series.plot(legend="Hours Worked", kind="bar")
    df[["Minimum Hours Required per day", "Optimal Hours Required per day"]].plot(ax=ax)
                     
def hours_worked_stats(daily_hrs, num_days: int=7, median=False) -> None:
    """Hours you've put in in the last {num_days}days. 
    
    Params
    -----
    median: if median, the average metric used is median, otherwise, mean is used
    """
    assert type(num_days) == int, "num_days not an interger"
    considered_hrs = daily_hrs[-num_days:]
    considered_period = len(considered_hrs)
    total_hrs = sum(considered_hrs)
    average_hrs = statistics.median(considered_hrs) if median else statistics.mean(considered_hrs)
    custom_print(f"Number of hours you put in in the last {considered_period}days", f"Total: {round(total_hrs, 2)}hrs", f"On Average: {round(average_hrs, 2)}hrs per day", sep="\n")

def get_actual_owes(owes, return_owed: Literal["include", "discard", "only_owed"]="include", return_free_time: Literal["include", "discard", "only_free_time"]="include") -> dict:
    """
    Calculates actual owed amounts based on specified criteria.

    Args:
        owes (dict): A dictionary of owed amounts.
        only_owed (str or bool): Specifies whether to include only owed tasks ("include"), exclude them ("discard") or return only them("only_owed").
        free_time (str): Specifies whether to include time owed to freetime ("include"), exclude them("discard") or return only them("only_free_time")

    Returns:
        dict: A dictionary containing the calculated actual owed amounts.
    """

    def reverse_key(key):
        return "To".join(key.split("To")[::-1])

    actual_owes = {}

    for key, value in owes.items():
        if "To" in key:
            rev = reverse_key(key)
            if rev in owes:
                if key.split("To")[0] == key.split("To")[1]:
                    continue
                if owes[rev] < value:
                    actual_owes[rev] = - abs(abs(owes[rev]) - abs(value))
                else:
                    actual_owes[key] = - abs(abs(value) - abs(owes[rev] ))
            else:
                actual_owes[key] = value
        else:
            actual_owes[key] = value

    for key, value in owes.items():
        if "To" in key and key.split("To")[0] == key.split("To")[1]:
            actual_owes[key.split("To")[0]] = abs(abs(owes[key.split("To")[0]]) - abs(value))

    filter_functions_owed = {
        "include": lambda x: True,
        "discard": lambda x: "To" not in x,
        "only_owed": lambda x: "To" in x,
    }
    filter_functions_freetime = {
        "include": lambda x: True,
        "discard": lambda x: "FreeTime" not in x,
        "only_free_time": lambda x: "FreeTime" in x,
    }
    actual_owes = {key: value for key, value in actual_owes.items() if filter_functions_owed[return_owed](key) and filter_functions_freetime[return_free_time](key)}

    return actual_owes
                    
def print_actual_owes_explanation():
    print("shows a list of all the tasks you owe time on. \nIt returns this list in the format of: \n",)
    print("Coding 23", "ReadingToFarmwork -4", "CodingToFreeTime -2", "Movies -23", "...", sep="\n")  
    print("Using the above format, this is the way to understand it.\n In the  first part(Coding 23), It means you were supposed to spend 23hrs coding which you didnt do and, as such, you owe 23hrs worth of work to coding. The higher the number, the more necessary it is to spend time on it. \nIn the second part(ReadingToFarmwork -4), it means you were supposed to spend 4hrs on Farmwork but instead, used the time allocated to it on a different task, in this case, you used it instead to Read(Reading). Hence you can take out time allocated to Reading for Farmwork. \nIn the third pard, it means you were supposed to spend 2hrs doing any other thing you want(which is not work, hence  the name FreeTime) but instead, spent the time working. in this case, you were coding when it was supposed to be your FreeTime. In future, you can take out time allocated to Coding for your FreeTime.\nIn the fourth section, It means you spent more time on the task than required/expected and as such, it owes you. In future, you can take out time allocated to this task(in this case, Movies) to do any other thing you want to. No strings attached.\n\nData is returned in this order.\n")
    print("Please Note: There's currently no way to track the free time you have used up so use TaskToFreeTime minimally, A good rule of thumb is to make sure you don't owe any task before you enjoy TaskToFreeTime Hrs", file=sys.stderr)

                     
def remove_day_attachments(date_string):
    date_string_temp = date_string.replace("August", "temp").replace("th ", \
            " ").replace("rd ", " ").replace("nd ", " ").replace("st ", " ")
    return date_string_temp.replace("temp", "August")
                      
def frame_object(dict_obj, dates):
    """Todo: Provide better name"""
    df = pd.DataFrame(dict_obj)
    df.index = pd.to_datetime(pd.Series(dates).apply(remove_day_attachments), dayfirst=True, format="%A %d %B %Y")
    #https://stackoverflow.com/questions/64955124/dataframe-plot-remove-time-from-x-axis-keeping-the-date-values
    df.index = df.index.date
    return df.fillna(0)

def get_considered_period(df, start_from=None, stop_at=None):
    start_from_dt = pd.to_datetime(start_from).date() if start_from else df.index[0]
    stop_at_dt = pd.to_datetime(stop_at).date() if stop_at else df.index[-1]
    return df[start_from_dt:stop_at_dt]

def get_timetable(file_path):
    return joblib.load(file_path)
    
                     
