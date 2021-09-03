from otree.api import *

c = Currency

doc = """
Real effort task, based on moving sliders, as in:
Gill, David, and Victoria Prowse. 2012.
"A Structural Analysis of Disappointment Aversion in a Real Effort Competition."
American Economic Review, 102 (1): 469-503.
DOI: 10.1257/aer.102.1.469
"""


class Constants(BaseConstants):
    name_in_url = 'sliders_task'
    players_per_group = None
    num_rounds = 1

    # Set task parameters
    sliders_task_pms = dict(
        time_in_seconds=60 * 2,
        num=48, columns=3,
        max=100, min=0,
        target=50,
        default='min',          # Sliders default value when the task begin
        num_centered=0,
        bonus_per_slider=cu(1),
        bonus=cu(0)
    )


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    num_centered = models.IntegerField()


# FUNCTIONS
def set_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def set_sliders_task(const: Constants):
    # Import module needed
    from random import randint, choice

    # Copy task parameters from Constants (which therefore will remain unchanged)
    task = const.sliders_task_pms.copy()

    # Set random value for left margin of sliders in each row
    offsets = [randint(0, 10) for _ in range(task['num'] // task['columns'])]

    # Set default values of sliders: either to "min" or to random values
    if task['default'] == 'min':
        m = task['min']
        curr_values = [m for _ in range(task['num'])]
    else:
        input_range = list(range(task['min'], task['max']))
        input_range.remove(task['target'])
        curr_values = [choice(input_range) for _ in range(task['num'])]

    # Set list of rows containing the sliders: each row contains 3 sliders and the left margin for that row
    sliders = list(zip(set_chunks(curr_values, task['columns']), offsets))

    # Flag task as set
    task_set = True

    # Update dictionary containing task parameters
    task.update(offsets=offsets, curr_values=curr_values, sliders=sliders)

    return task_set, task


# PAGES
class SliderTask(Page):
    timeout_seconds = Constants.sliders_task_pms['time_in_seconds']
    timer_text = 'Remaining time: '

    @staticmethod
    def vars_for_template(player: Player):
        pvars = player.participant.vars
        # If no task exists yet, set a new task
        if not pvars.get('sliders_task_set'):
            pvars['sliders_task_set'], pvars['sliders_task'] = set_sliders_task(Constants)

        # Returns the dictionary containing the task parameters as variables for the template
        return pvars['sliders_task']

    @staticmethod
    def live_method(player: Player, data):
        participant = player.participant

        # Get task parameters
        task = participant.vars['sliders_task']

        # Get updated number of centered sliders
        num_centered = len([v for v in data if v == task['target']])

        # Update task parameters based on: current values of the sliders, number of centered sliders, bonus accumulated
        task.update(
            sliders=list(zip(set_chunks(data, task['columns']), task['offsets'])),
            num_centered=num_centered,
            bonus=num_centered * task['bonus_per_slider']
        )

        # Send updated task's parameters to the webpage
        return {player.id_in_group: dict(num_centered=num_centered, bonus=task['bonus'])}

    # Set player fields with number of centered sliders and payoff
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        task = player.participant.vars['sliders_task']
        player.num_centered = task['num_centered']
        player.payoff = task['bonus']

class PreRet(Page):
    pass

page_sequence = [PreRet, SliderTask]