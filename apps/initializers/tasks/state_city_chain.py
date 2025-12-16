from celery import chain

from apps.initializers.tasks import initialize_states_task, initialize_state_cities_task


def start_city_and_state_task_chain():
    # Chain tasks
    task_chain = chain(initialize_states_task.si(), initialize_state_cities_task.si())
    task_chain.delay()
