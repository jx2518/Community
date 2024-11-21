import logging
import numpy as np
from itertools import combinations


# Global static variables
WEAKNESS_THRESHOLD = 5          # Percentile threshold for weakest player
LOWEST_COST_THRESHOLD = 90     # Percentile threshold for volunteering


# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    handlers=[
        logging.FileHandler("log-results/team4_log.log", mode='w'),
        logging.StreamHandler()
    ]
)


def phaseIpreferences(player, community, global_random):
    '''Return a list of task index and the partner id for the particular player. The output format should be a list of lists such that each element
    in the list has the first index task [index in the community.tasks list] and the second index as the partner id'''
    list_choices = []

    # Print member abilities and task difficulty
    # for member in community.members:
    #     logging.debug(f"Member {member.id} abilities: {member.abilities}")
    # for task in community.tasks:
    #     logging.debug(f"Task: {task}")

    # Calculate cost matrices
    cost_matrix_individual, cost_matrix_pairs = calculate_cost_matrix(community)

    # Rank assignment options by task
    list_of_ranked_assignments = get_ranked_assignments(community, cost_matrix_individual,
                                                        cost_matrix_pairs)

    for t in range(len(list_of_ranked_assignments)):
        # Exhausting tasks (energy required >= 20)
        # Return and volunteer alone in Phase II
        if list_of_ranked_assignments[t][0][1] >= 20:
            if is_weakest_player(player, community):
                return list_choices

        # Tiring tasks (10 <= energy required < 20)
        # Wait until energy is full to volunteer with a partner
        elif 10 < list_of_ranked_assignments[t][0][1] < 20:
            for assignment in list_of_ranked_assignments[t]:
                if player.id in assignment[0] and None not in assignment[0] and player.energy == 10:                    
                    partner_id = assignment[0][0] if player.id == assignment[0][1] else assignment[0][1]
                    list_choices.append([t, partner_id])

        # Easier tasks (energy required < 10)
        # Volunteer to partner as long as energy >= task cost
        else:
            for assignment in list_of_ranked_assignments[t]:
                if player.id in assignment[0] and None not in assignment[0] and player.energy >= assignment[1]:
                    partner_id = assignment[0][0] if player.id == assignment[0][1] else assignment[0][1]
                    list_choices.append([t, partner_id])

    return list_choices


def phaseIIpreferences(player, community, global_random):
    '''Return a list of tasks for the particular player to do individually'''
    bids = []

    # Calculate cost matrices
    cost_matrix_individual, cost_matrix_pairs = calculate_cost_matrix(community)

    # Rank assignment options by task
    list_of_ranked_assignments = get_ranked_assignments(community, cost_matrix_individual,
                                                        cost_matrix_pairs)

    for t in range(len(list_of_ranked_assignments)):
        # Exhausting tasks (energy required >= 20)
        # Volunteer to sacrifice
        if list_of_ranked_assignments[t][0][1] >= 20:
            if is_weakest_player(player, community):
                bids.append(t)
                return bids

        # Easier tasks (energy required < 10)
        # Volunteer to partner as long as energy >= task cost
        elif list_of_ranked_assignments[t][0][1] <= 10:
            for assignment in list_of_ranked_assignments[t]:
                if player.id in assignment[0] and None in assignment[0] and player.energy >= assignment[1]:
                    bids.append(t)

    return bids


def calculate_cost_matrix(community):
    """
    Calculates the cost matrices for individual members and pairs based on abilities and tasks.
    """
    tasks = community.tasks
    members = community.members

    # Individual costs
    cost_matrix_individual = {}
    for member in members:
        for t, task in enumerate(tasks):
            cost = sum([max(0, task[i] - member.abilities[i]) for i in range(len(member.abilities))])
            cost_matrix_individual[(member.id, t)] = cost

    # Pair costs
    cost_matrix_pairs = {}
    for member1, member2 in combinations(members, 2):
        for t, task in enumerate(tasks):
            combined_abilities = np.maximum(member1.abilities, member2.abilities)
            cost = sum([max(0, task[i] - combined_abilities[i])
                        for i in range(len(combined_abilities))]) / 2  # Half cost for shared work
            cost_matrix_pairs[(member1.id, member2.id, t)] = cost

    return cost_matrix_individual, cost_matrix_pairs


def get_ranked_assignments(community, cost_matrix_individual, cost_matrix_pairs):
    """
    Rank assignments of paired and individual workers for each task based on the cost matrices.
    """
    tasks = community.tasks
    members = community.members
    
    list_of_ranked_assignments = []

    for t in range(len(tasks)):
        assignments = {}
        for member in members:
            assignments[(member.id, None)] = cost_matrix_individual[(member.id, t)]
        for member1, member2 in combinations(members, 2):
            assignments[(member1.id, member2.id)] = cost_matrix_pairs[(member1.id, member2.id, t)]

        ranked_assignments_dict = dict(sorted(assignments.items(), key=lambda item: item[1]))
        ranked_assignments = list(ranked_assignments_dict.items())
        list_of_ranked_assignments.append(ranked_assignments)

    return list_of_ranked_assignments


def is_weakest_player(player, community):
    sum_of_abilities = []
    
    for member in community.members:
        sum_of_abilities.append(sum(member.abilities))

    sorted_abilities = np.array(sorted(sum_of_abilities))
    threshold = np.percentile(sorted_abilities, WEAKNESS_THRESHOLD)
    
    return sum(player.abilities) < threshold

