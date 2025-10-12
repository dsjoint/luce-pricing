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

###############################################################################
############### code for sampling permutations based on weights ###############
###############################################################################

def get_ordering_distribution(population, weights, iterations, normalize=True):
    table = defaultdict(int)
    size = len(population)

    for _ in range(iterations):
        ord = tuple(weighted_sample_without_replacement(population, weights, size)) # sample an ordering
        table[ord] += 1
    
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

def final_show_table(pool, iterations=100000):
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

# Example usage

win_pool = {
    "Diamond's Honor" : 456, 
    "Queen McKinzie" : 2103, 
    "Sunna" : 595, 
    "Sapphire Girl" : 530, 
    "Tapit's Mischief" : 591
}

show_pool = {
    "Diamond's Honor" : 102, 
    "Queen McKinzie" : 402, 
    "Sunna" : 86, 
    "Sapphire Girl" : 90, 
    "Tapit's Mischief" : 64
}

print(get_relative_pool(show_pool))

print(final_show_table(win_pool, 100000))