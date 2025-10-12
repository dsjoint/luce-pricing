pool = {"Vino" : 3.79, "Burning" : 23.39, "Salient" : 2.43, "Kiddo" : 2.18, "Golden" : 9.87, "Reno" : 39.02, "Grayson" : 7.32, "Beneficial" : 12}

def weighted_sample(pool):
    import random
    total = sum(pool.values())
    rand_val = random.uniform(0, total)
    cumulative = 0
    for key, weight in pool.items():
        cumulative += weight
        if rand_val < cumulative:
            return key
        
def weighted_sample_without_replacement(pool):
    resulting_permutation = []
    pool_copy = pool.copy()
    while pool_copy:
        selected = weighted_sample(pool_copy)
        resulting_permutation.append(selected)
        del pool_copy[selected]
    return resulting_permutation

def permutation_table(pool, iterations):
    from collections import defaultdict
    table = defaultdict(int)
    for _ in range(iterations):
        perm = tuple(weighted_sample_without_replacement(pool))
        table[perm] += 1
    return dict(table)

def probability_of_show(horse, iterations, table):
    count = 0
    for perm, freq in table.items():
        if horse in perm[:3]:
            count += freq
    return count / iterations

def probability_of_show_table(iterations):
    table = permutation_table(pool, iterations)
    results = {}
    for horse in pool.keys():
        results[horse] = probability_of_show(horse, iterations, table)
    return results

def renormalize_show_table(show_table):
    total = sum(show_table.values())
    # Round all probabilities to 2 decimal points after renormalizing
    return {horse: round(prob * 100 / total, 2) for horse, prob in show_table.items()}

def final_show_table(iterations):
    t = probability_of_show_table(iterations)
    return renormalize_show_table(t)

print(final_show_table(100000))