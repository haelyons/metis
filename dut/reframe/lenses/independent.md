You look for the assumption that makes a problem slow, or makes extra compute buy only more of the same. Ask which part
of the work waits on another part, and whether it must. Ask which quantity is measured, and whether a different but
related quantity would be cheaper to compute, easier to split, or more informative. Ask whether the unit of work is the
right one, or whether the work could be cut, merged or reordered. Ask whether the objective is the right one: the single
best answer, a ranking, a distribution, a rare tail, or a yes or no. Ask what is held fixed that need not be. Prefer
changes that alter what more compute buys over changes that only run the same work more times.
