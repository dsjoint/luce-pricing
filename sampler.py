import random
from collections import defaultdict

# Helper functions
def dict_to_list(pool):
    return list(pool.keys()), list(pool.values())

def weighted_sample_without_replacement(population, weights, k):
    sample = []
    
    if k > len(population):
        raise ValueError("Sample size k cannot be greater than the population size.")
    
    population_copy = population[:]
    weights_copy = weights[:]

    for _ in range(k):
        selected = random.choices(population_copy, weights=weights_copy, k=1)[0]
        sample.append(selected)
        index = population_copy.index(selected)
        del population_copy[index]
        del weights_copy[index]
    
    return sample

def print_dictionary(d):
    for key, value in d.items():
        print(f"{key}: {value:.4f}")

###############################################################################
############### code for sampling permutations based on weights ###############
###############################################################################

def get_ordering_frequency(population, weights, iterations):
    table = defaultdict(int)
    size = len(population)

    for _ in range(iterations):
        ord = tuple(weighted_sample_without_replacement(population, weights, size)) # sample an ordering
        table[ord] += 1
    return table

def get_ordering_distribution(population, weights, iterations, normalize=True):
    table = get_ordering_frequency(population, weights, iterations)
    
    # normalize the table to get probabilities
    if normalize:
        for ord in table:
            table[ord] /= iterations

    return table

def probability_of_show(horse, table):
    total_prob = 0
    for perm, prob in table.items():
        if horse in perm[:3]:
            total_prob += prob
    return total_prob/3

def get_show_table(pool, iterations=100000):
    population, weights = dict_to_list(pool)
    table = get_ordering_distribution(population, weights, iterations)
    results = {}
    for element in population:
        results[element] = probability_of_show(element, table)

    return results

###############################################################################
########################## code for comparing tables ##########################
###############################################################################

def get_probability_table(pool, iterations=100000):
    population, weights = dict_to_list(pool)
    return get_ordering_distribution(population, weights, iterations)

def get_relative_pool(base_pool):
    relative_pool = {}
    total = sum(base_pool.values())
    for element, weight in base_pool.items():
        relative_pool[element] = weight / total
    return relative_pool

# compute expected winnings based on parimutuel payouts for show
def get_parimutuel_payout(pool, ordering_prob, show_pool):
    population, weights = dict_to_list(pool)
    parimutuel_payout = defaultdict(float)
    total_show_pool = sum(show_pool.values())

    for candidate in population:
        payout = 0
        for ord, prob in ordering_prob.items():
            if candidate not in ord[:3]:
                continue

            top3_total = sum(show_pool[horse] for horse in ord[:3])
            if top3_total <= 0:
                continue

            payout += (total_show_pool / top3_total) * prob # this computes expected *total return* not just winnings
        parimutuel_payout[candidate] = payout - 1 # subtract the 1 you bet to get expected winnings
    return parimutuel_payout

def get_odds_payout(pool, ordering_prob, odds): # odds is a dict of horse -> odds (e.g., 4 means you win 4 for every 1 you bet)
    population, weights = dict_to_list(pool)
    odds_payout = defaultdict(float)

    for candidate in population:
        payout = 0
        for ord, prob in ordering_prob.items():
            if candidate not in ord[:3]:
                continue

            payout += odds[candidate] * prob # this computes expected *winnings* not total return
        
        odds_payout[candidate] = payout

    return odds_payout

def get_projected_expectation(pool, method='parimutuel', iterations=100000, show_pool=None, odds=None):
    expectation = defaultdict(float)
    population, weights = dict_to_list(pool)
    ordering_prob = get_ordering_distribution(population, weights, iterations)

    if method == 'parimutuel':
        if show_pool is None:
            raise ValueError("show_pool must be provided for parimutuel method.")
        expectation = get_parimutuel_payout(pool, ordering_prob, show_pool)

    elif method == 'odds':
        if odds is None:
            raise ValueError("odds must be provided for odds method.")
        expectation = get_odds_payout(pool, ordering_prob, odds)

    else:
        raise ValueError("Method must be either 'parimutuel' or 'odds'.")
    
    return dict(expectation)

def run_analysis(pool, show_pool):
    print("Relative Show Pool Distribution:")
    print("-")
    relative_show_pool = get_relative_pool(show_pool)
    print_dictionary(relative_show_pool)
    print("---")

    print("Projected Show Probabilities:")
    print("-")
    show_table = get_show_table(pool, 100000)
    print_dictionary(show_table)
    print("---")

    print("Projected Expected Earnings (Parimutuel):")
    print("-")
    projected_exp = get_projected_expectation(pool, method='parimutuel', iterations=100000, show_pool=show_pool)
    print_dictionary(projected_exp)


###########################################################################
###################### Code for importing jsonl data ######################
###########################################################################

def jsonl_to_dicts(filename):
    import json
    dicts = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            dicts.append(json.loads(line))
    return dicts

def snapshot_to_pools(snapshot):
    win_pool = {}
    show_pool = {}
    for entry in snapshot['entries']:
        horse = entry['horse']
        if entry['win_pool'] is None or entry['show_pool'] is None:
            continue
        else:
            win_pool[horse] = entry['win_pool']
            show_pool[horse] = entry['show_pool']
    return win_pool, show_pool






if __name__ == "__main__":
    snapshots = jsonl_to_dicts("live_odds_snapshots.jsonl")
    latest_snapshot = snapshots[-1]

    win_pool, show_pool = snapshot_to_pools(latest_snapshot)
    print(f"Track: {latest_snapshot['track']}, Race Number: {latest_snapshot['race_number']}")

    run_analysis(win_pool, show_pool)
