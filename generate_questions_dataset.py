"""
Generate database/queries/questions.sql with ~400 grouped interview questions.
Run: python generate_questions_dataset.py
Then: python load_questions.py && python generate_embeddings.py
"""

import json
from datetime import date
from pathlib import Path

OUTPUT = Path("database/queries/questions.sql")
TODAY = date.today().isoformat()
ROLE = ["Software Engineer"]
QUESTIONS_PER_GROUP = 4  # 1 entry + 3 follow-ups
DIFF_PATTERN = ["easy", "easy", "medium", "hard"]


def g(group_id, topic, category, items):
    """Build one question group (entry + up to 3 follow-ups)."""
    trimmed = items[:QUESTIONS_PER_GROUP]
    return {
        "id": group_id,
        "topic": topic,
        "category": category,
        "questions": [
            {"text": text, "diff": diff, "kw": kw}
            for text, diff, kw in zip(
                [i[0] for i in trimmed],
                [i[1] if len(i) > 1 else DIFF_PATTERN[idx] for idx, i in enumerate(trimmed)],
                [i[2] if len(i) > 2 else [] for i in trimmed],
            )
        ],
    }


# Each item: (question_text, difficulty optional, keywords)
DSA_GROUPS = [
    g("DSA_ARRAYS_01", "DSA", "technical", [
        ("What is an array and what are its core properties regarding memory layout and index access?", "easy", ["contiguous memory", "zero-based index", "fixed size"]),
        ("What is the time complexity of accessing an element by index in an array?", "easy", ["O(1)", "direct addressing", "index lookup"]),
        ("What is the time complexity of inserting an element at the beginning of a static array?", "medium", ["O(n)", "element shifting", "insertion cost"]),
        ("What is the difference between a static array and a dynamic array regarding size and resizing?", "medium", ["fixed capacity", "amortized resizing", "heap allocation"]),
        ("Given an array of integers, what algorithm finds the maximum subarray sum in O(n) time?", "hard", ["Kadane algorithm", "dynamic tracking", "linear scan"]),
    ]),
    g("DSA_ARRAYS_02", "DSA", "technical", [
        ("What is a two-pointer technique when applied to sorted arrays?", "easy", ["pair of indices", "sorted input", "simultaneous traversal"]),
        ("How does the two-pointer approach solve the pair-sum problem on a sorted array in O(n) time?", "medium", ["left right pointers", "sum comparison", "linear traversal"]),
        ("What is the sliding window technique and when is it applicable on arrays?", "medium", ["contiguous subarray", "window expansion", "fixed or variable size"]),
        ("What is the time complexity of finding the maximum sum subarray of size k using a sliding window?", "medium", ["O(n)", "window slide", "sum update"]),
        ("How do prefix sums enable O(1) range sum queries after O(n) preprocessing?", "hard", ["cumulative sum array", "range difference", "precomputation"]),
    ]),
    g("DSA_ARRAYS_03", "DSA", "technical", [
        ("What is array rotation and how many elements move when rotating an array by k positions?", "easy", ["cyclic shift", "modulo index", "k positions"]),
        ("What is the time complexity of reversing an array in place?", "easy", ["O(n)", "swap pairs", "in-place"]),
        ("How can you rotate an array by k steps in O(n) time using the reverse method?", "medium", ["triple reverse", "modulo k", "in-place rotation"]),
        ("What is the time and space complexity of merging two sorted arrays into one sorted array?", "medium", ["O(n+m)", "two pointers", "auxiliary space"]),
        ("What algorithm finds the kth largest element in an unsorted array in O(n) average time?", "hard", ["quickselect", "partition", "order statistic"]),
    ]),
    g("DSA_STRINGS_01", "DSA", "technical", [
        ("What is a string in programming and how is it typically stored in memory?", "easy", ["character sequence", "byte encoding", "null terminator or length"]),
        ("What is the time complexity of comparing two strings of length n character by character?", "easy", ["O(n)", "lexicographic compare", "per character"]),
        ("What algorithm checks whether a string is a palindrome in O(n) time?", "medium", ["two pointers", "mirror check", "linear scan"]),
        ("What is the difference between immutable and mutable string types regarding concatenation cost?", "medium", ["copy on concat", "builder pattern", "amortized cost"]),
        ("How does the Rabin-Karp algorithm use rolling hash for substring search and what is its average time complexity?", "hard", ["rolling hash", "O(n)", "hash collision"]),
    ]),
    g("DSA_STRINGS_02", "DSA", "technical", [
        ("What is the brute-force time complexity of finding a pattern of length m in a text of length n?", "easy", ["O(nm)", "nested loops", "substring check"]),
        ("How does the KMP algorithm avoid redundant comparisons using a prefix function?", "medium", ["prefix LPS array", "pattern preprocessing", "O(n+m)"]),
        ("What information does the LPS (longest prefix suffix) array store in KMP?", "medium", ["border length", "prefix suffix match", "failure pointer"]),
        ("What is the overall time complexity of KMP pattern matching?", "medium", ["O(n+m)", "linear scan", "preprocessing"]),
        ("When would you choose KMP over brute-force string matching for long repetitive patterns?", "hard", ["repeated prefixes", "backtracking avoidance", "worst-case linear"]),
    ]),
    g("DSA_STRINGS_03", "DSA", "technical", [
        ("What is an anagram and how can you verify two strings are anagrams using sorting?", "easy", ["same characters", "sort compare", "O(n log n)"]),
        ("How can frequency counting verify anagrams in O(n) time?", "medium", ["character histogram", "count array", "linear time"]),
        ("What algorithm finds the longest common prefix among an array of strings?", "medium", ["vertical scanning", "shared prefix", "early termination"]),
        ("What is the time complexity of finding the longest palindromic substring using expand-around-center?", "medium", ["O(n^2)", "center expansion", "palindrome check"]),
        ("How does Manacher's algorithm find all palindromes in O(n) time?", "hard", ["mirroring centers", "radius array", "linear palindrome"]),
    ]),
    g("DSA_SEARCH_01", "DSA", "technical", [
        ("What is searching in the context of data structures?", "easy", ["element lookup", "key comparison", "search space"]),
        ("What are the main categories of searching algorithms on sequential data?", "easy", ["linear search", "binary search", "interpolation search"]),
        ("Explain linear search and state its worst-case time complexity.", "medium", ["sequential scan", "O(n)", "unordered data"]),
        ("Explain binary search and state its time complexity and input prerequisite.", "medium", ["sorted array", "O(log n)", "divide midpoint"]),
        ("What is the key difference between linear search and binary search in terms of input requirements and time complexity?", "hard", ["sorted requirement", "O(n) vs O(log n)", "comparison count"]),
    ]),
    g("DSA_SEARCH_02", "DSA", "technical", [
        ("What precondition must hold for binary search to correctly locate a target?", "easy", ["sorted order", "comparable elements", "monotonic arrangement"]),
        ("How do you compute the middle index in binary search to avoid integer overflow?", "medium", ["low plus high divide", "unsigned shift", "overflow safe"]),
        ("How do you modify binary search to find the first occurrence of a duplicate target?", "medium", ["bias left", "lower bound", "boundary tracking"]),
        ("What is lower bound binary search and what index does it return?", "medium", ["first >= target", "insertion position", "sorted bounds"]),
        ("Why does binary search fail on a rotated sorted array without modification?", "hard", ["broken monotonicity", "pivot rotation", "partition logic needed"]),
    ]),
    g("DSA_SEARCH_03", "DSA", "technical", [
        ("How can you search a target in a rotated sorted array in O(log n) time?", "medium", ["pivot detection", "partitioned binary search", "range check"]),
        ("What is interpolation search and how does it estimate the probe index?", "medium", ["uniform distribution", "proportional index", "formula estimate"]),
        ("Under what data distribution does interpolation search achieve O(log log n) average time?", "medium", ["uniformly spaced", "linear distribution", "even spread"]),
        ("What is the worst-case time complexity of interpolation search?", "hard", ["O(n)", "skewed data", "poor probe estimates"]),
        ("How does exponential search locate a target in an unbounded sorted array?", "hard", ["exponential bounds", "doubling index", "binary search phase"]),
    ]),
    g("DSA_SORT_01", "DSA", "technical", [
        ("What is sorting and what does stability mean for a sorting algorithm?", "easy", ["ordering elements", "stable sort", "equal element order"]),
        ("What is the time complexity of bubble sort in the worst case?", "easy", ["O(n^2)", "adjacent swaps", "nested passes"]),
        ("What is the time complexity of selection sort and why?", "medium", ["O(n^2)", "minimum selection", "fixed comparisons"]),
        ("What is the average and worst-case time complexity of insertion sort?", "medium", ["O(n^2) worst", "O(n) best", "adaptive"]),
        ("Which simple quadratic sorts are in-place and which require extra memory?", "hard", ["in-place swaps", "auxiliary array", "memory tradeoff"]),
    ]),
    g("DSA_SORT_02", "DSA", "technical", [
        ("Explain the divide-and-conquer approach of merge sort.", "easy", ["split halves", "merge sorted", "recursive"]),
        ("What is the time and space complexity of merge sort?", "medium", ["O(n log n)", "auxiliary array", "stable"]),
        ("What is the average and worst-case time complexity of quicksort?", "medium", ["O(n log n) average", "O(n^2) worst", "partition based"]),
        ("What pivot strategy reduces quicksort worst-case on sorted input?", "medium", ["random pivot", "median of three", "balanced partition"]),
        ("What is the Dutch National Flag algorithm used for in sorting?", "hard", ["three-way partition", "duplicate keys", "O(n) duplicates"]),
    ]),
    g("DSA_SORT_03", "DSA", "technical", [
        ("How does heap sort achieve O(n log n) worst-case time using a binary heap?", "medium", ["heapify", "extract max", "in-place"]),
        ("Is heap sort stable and what is its typical space complexity?", "medium", ["not stable", "O(1) space", "in-place"]),
        ("What is counting sort and what constraint applies to input keys?", "medium", ["integer keys", "small range", "O(n+k)"]),
        ("How does radix sort process digits or characters to sort in O(nk) time?", "medium", ["digit passes", "stable sub-sort", "place value"]),
        ("What is the lower bound time complexity for comparison-based sorting of n elements?", "hard", ["Omega(n log n)", "decision tree", "comparison bound"]),
    ]),
    g("DSA_LINKED_01", "DSA", "technical", [
        ("What is a linked list and how does it differ from an array in memory layout?", "easy", ["nodes and pointers", "non-contiguous", "dynamic size"]),
        ("What is the time complexity of inserting at the head of a singly linked list?", "easy", ["O(1)", "pointer update", "head insert"]),
        ("What is the time complexity of searching for a value in a singly linked list?", "medium", ["O(n)", "sequential traversal", "no indexing"]),
        ("How do you detect a cycle in a linked list in O(n) time and O(1) space?", "medium", ["Floyd cycle", "two pointers", "tortoise hare"]),
        ("What is the time complexity of reversing a singly linked list in place?", "medium", ["O(n)", "pointer reversal", "iterative"]),
    ]),
    g("DSA_LINKED_02", "DSA", "technical", [
        ("What is a doubly linked list and what extra operation does it enable versus singly linked?", "easy", ["prev pointer", "backward traversal", "delete node"]),
        ("How do you merge two sorted linked lists into one sorted list in O(n+m) time?", "medium", ["two pointers", "dummy head", "linear merge"]),
        ("What is the middle node of a linked list and how do you find it with one pass?", "medium", ["slow fast pointers", "half speed", "O(n)"]),
        ("How do you remove the nth node from the end of a linked list in one pass?", "medium", ["two pointer gap", "nth ahead", "single traversal"]),
        ("What is the time complexity of inserting at a known node in a singly linked list without head reference?", "hard", ["O(1) after locate", "O(n) search", "pointer splice"]),
    ]),
    g("DSA_STACK_01", "DSA", "technical", [
        ("What is a stack ADT and what are its two primary operations?", "easy", ["push pop", "LIFO", "top element"]),
        ("What is the time complexity of push and pop on a stack implemented with a dynamic array?", "easy", ["O(1) amortized", "array stack", "top index"]),
        ("How can two stacks be implemented using one array?", "medium", ["split array", "two tops", "shared buffer"]),
        ("What classic problem uses a stack to validate balanced parentheses?", "medium", ["matching pairs", "open close stack", "O(n) scan"]),
        ("How does a stack support iterative depth-first traversal of a graph?", "hard", ["LIFO exploration", "push neighbors", "DFS order"]),
    ]),
    g("DSA_STACK_02", "DSA", "technical", [
        ("How do you evaluate an arithmetic expression in postfix notation using a stack?", "medium", ["operand stack", "operator apply", "RPN evaluation"]),
        ("What is the monotonic stack technique used for in array problems?", "medium", ["next greater element", "maintain order", "linear scan"]),
        ("What problem does a monotonic decreasing stack solve for daily temperatures?", "medium", ["next warmer day", "index distance", "O(n)"]),
        ("How can stacks simulate queue operations using two stacks?", "hard", ["in stack out stack", "amortized O(1)", "queue simulation"]),
        ("What is the space complexity of recursive DFS versus explicit stack DFS on a graph?", "hard", ["recursion stack", "explicit stack", "O(depth)"]),
    ]),
    g("DSA_QUEUE_01", "DSA", "technical", [
        ("What is a queue ADT and what are enqueue and dequeue?", "easy", ["FIFO", "front rear", "enqueue dequeue"]),
        ("What is the time complexity of enqueue and dequeue in a circular array queue?", "easy", ["O(1)", "circular buffer", "modulo wrap"]),
        ("How does a circular queue avoid wasted space in a fixed array implementation?", "medium", ["wrap indices", "reuse slots", "front rear modulo"]),
        ("What is a deque and what operations does it support?", "medium", ["double ended", "push pop both ends", "O(1) ends"]),
        ("How does BFS use a queue to traverse a graph level by level?", "medium", ["FIFO layers", "visited set", "shortest unweighted path"]),
    ]),
    g("DSA_QUEUE_02", "DSA", "technical", [
        ("What is the time complexity of BFS on a graph with V vertices and E edges?", "medium", ["O(V+E)", "visit each edge", "queue processing"]),
        ("How do you implement a queue using two stacks?", "medium", ["in out stacks", "amortized O(1)", "FIFO from LIFO"]),
        ("What is a priority queue and how is it different from a regular queue?", "medium", ["priority ordering", "heap backed", "not FIFO"]),
        ("What data structure typically implements a priority queue with O(log n) insert and extract?", "medium", ["binary heap", "heapify", "logarithmic ops"]),
        ("When does BFS guarantee shortest path in an unweighted graph?", "hard", ["non-negative edges", "unit weight", "first visit shortest"]),
    ]),
    g("DSA_TREES_01", "DSA", "technical", [
        ("What is a binary tree and what is the maximum number of nodes at depth d?", "easy", ["two children", "2^d nodes", "tree depth"]),
        ("What are the three standard depth-first traversal orders of a binary tree?", "easy", ["inorder preorder postorder", "DFS orders", "node visit"]),
        ("What is the time complexity of traversing all nodes in a binary tree?", "medium", ["O(n)", "visit each node", "traversal"]),
        ("What is the height of a balanced binary tree with n nodes?", "medium", ["O(log n)", "balanced property", "tree height"]),
        ("What is the difference between a full, complete, and perfect binary tree?", "hard", ["node fill rules", "level completeness", "definitions"]),
    ]),
    g("DSA_TREES_02", "DSA", "technical", [
        ("What is a binary search tree (BST) invariant?", "easy", ["left less right greater", "ordered tree", "BST property"]),
        ("What is the average and worst-case time complexity of BST search?", "medium", ["O(log n) average", "O(n) skewed", "height dependent"]),
        ("How do you perform inorder traversal on a BST and what property does the output have?", "medium", ["sorted order", "left root right", "ascending values"]),
        ("What rotations are used to rebalance an AVL tree after insertion?", "medium", ["single double rotation", "balance factor", "height balance"]),
        ("What is the maximum height difference allowed between subtrees in an AVL tree?", "hard", ["balance factor 1", "height difference", "rebalance trigger"]),
    ]),
    g("DSA_TREES_03", "DSA", "technical", [
        ("What is a red-black tree and what color properties maintain balance?", "medium", ["red black colors", "five properties", "balanced BST"]),
        ("What is the time complexity of insert and search in a red-black tree?", "medium", ["O(log n)", "bounded height", "color fixup"]),
        ("What is a trie and what type of queries does it optimize?", "medium", ["prefix tree", "string prefix", "character nodes"]),
        ("What is the space complexity of a trie storing n strings of average length L?", "medium", ["O(nL)", "branching factor", "shared prefixes"]),
        ("When is a trie preferred over a hash map for string keys?", "hard", ["prefix queries", "autocomplete", "lexicographic range"]),
    ]),
    g("DSA_BST_01", "DSA", "technical", [
        ("How do you insert a new key into a BST while preserving the invariant?", "easy", ["compare descend", "leaf attach", "recursive insert"]),
        ("How do you delete a node with two children in a BST?", "medium", ["inorder successor", "swap replace", "two children case"]),
        ("What is the successor of a node in a BST?", "medium", ["min in right subtree", "next larger", "inorder next"]),
        ("What causes a BST to degenerate to O(n) height?", "hard", ["sorted insertion", "skewed tree", "no balancing"]),
        ("How do you verify whether a binary tree is a valid BST?", "medium", ["range bounds", "min max constraint", "recursive check"]),
    ]),
    g("DSA_HEAP_01", "DSA", "technical", [
        ("What is a binary heap and what is the heap property for a max heap?", "easy", ["parent greater children", "complete tree", "max heap"]),
        ("What is the index relationship between parent and children in a heap stored in an array?", "easy", ["parent i children 2i 2i+1", "array heap", "zero or one based"]),
        ("What is the time complexity of insert and extract-max in a binary heap?", "medium", ["O(log n)", "heapify up down", "bubble sift"]),
        ("What is heapify and what is its time complexity for building a heap from n elements?", "medium", ["bottom up heapify", "O(n)", "build heap"]),
        ("How does heapsort use a heap to sort in O(n log n) time?", "medium", ["extract max n times", "heapify", "in-place sort"]),
    ]),
    g("DSA_HEAP_02", "DSA", "technical", [
        ("What is a min heap and when is it used in Dijkstra's algorithm?", "medium", ["minimum extract", "priority queue", "shortest path"]),
        ("What is the difference between a binary heap and a Fibonacci heap in theoretical complexity?", "hard", ["amortized decrease key", "Dijkstra improvement", "Fibonacci heap"]),
        ("How do you find the k largest elements in an array using a heap of size k?", "medium", ["min heap k", "O(n log k)", "streaming top k"]),
        ("What is the time complexity of merging k sorted lists using a heap?", "medium", ["O(n log k)", "k-way merge", "heap min"]),
        ("Why is a heap preferred over a sorted array for a dynamic priority queue?", "hard", ["O(log n) updates", "dynamic insert", "no full sort"]),
    ]),
    g("DSA_GRAPH_01", "DSA", "technical", [
        ("What is a graph and how are directed and undirected graphs different?", "easy", ["vertices edges", "direction", "undirected mutual"]),
        ("What is the difference between adjacency matrix and adjacency list representations?", "easy", ["matrix O(V^2)", "list O(V+E)", "space tradeoff"]),
        ("What is the time complexity of BFS using an adjacency list?", "medium", ["O(V+E)", "visit vertices edges", "queue traversal"]),
        ("What is the time complexity of DFS using an adjacency list?", "medium", ["O(V+E)", "recursive stack", "edge exploration"]),
        ("What is a connected component in an undirected graph?", "medium", ["reachable subgraph", "maximal connected", "component count"]),
    ]),
    g("DSA_GRAPH_02", "DSA", "technical", [
        ("How does Dijkstra's algorithm find shortest paths in a graph with non-negative weights?", "medium", ["greedy expand", "priority queue", "non-negative"]),
        ("What is the time complexity of Dijkstra with a binary heap?", "medium", ["O((V+E) log V)", "heap extract", "edge relax"]),
        ("Why does Dijkstra fail with negative edge weights?", "hard", ["greedy assumption", "negative cycle", "relaxation order"]),
        ("What is the Bellman-Ford algorithm and its time complexity?", "hard", ["V-1 relaxations", "O(VE)", "negative edges"]),
        ("What does Floyd-Warshall compute and in what time complexity?", "hard", ["all pairs shortest", "O(V^3)", "DP on paths"]),
    ]),
    g("DSA_GRAPH_03", "DSA", "technical", [
        ("What is a topological sort and on which graph type is it defined?", "medium", ["DAG ordering", "precedence edges", "directed acyclic"]),
        ("How does Kahn's algorithm perform topological sort using in-degree?", "medium", ["BFS in-degree zero", "queue process", "O(V+E)"]),
        ("What is a strongly connected component in a directed graph?", "medium", ["mutual reachability", "SCC", "Kosaraju Tarjan"]),
        ("What algorithm finds SCCs in O(V+E) time?", "hard", ["Kosaraju", "two DFS passes", "transpose graph"]),
        ("What is the difference between BFS and DFS for detecting cycles in directed graphs?", "hard", ["back edge", "recursion stack", "cycle detection"]),
    ]),
    g("DSA_HASH_01", "DSA", "technical", [
        ("What is a hash table and what is the purpose of a hash function?", "easy", ["key to index", "hash function", "fast lookup"]),
        ("What is a collision in a hash table and what is chaining resolution?", "easy", ["same bucket", "linked list bucket", "collision"]),
        ("What is the average time complexity of search insert delete in a hash table with chaining?", "medium", ["O(1) average", "load factor", "chain length"]),
        ("What is open addressing and what is linear probing?", "medium", ["probe sequence", "next slot", "no chaining"]),
        ("What is the load factor and why must it be kept below a threshold?", "medium", ["n over m", "rehash trigger", "performance degrade"]),
    ]),
    g("DSA_HASH_02", "DSA", "technical", [
        ("What is double hashing in open addressing?", "medium", ["second hash step", "probe offset", "clustering reduction"]),
        ("Why does primary clustering occur in linear probing?", "hard", ["consecutive fills", "probe chains", "cluster formation"]),
        ("What properties make a good hash function for strings?", "medium", ["uniform distribution", "low collision", "deterministic"]),
        ("What is rehashing and when is it triggered?", "medium", ["resize table", "load factor threshold", "reinsert all"]),
        ("What is the worst-case time complexity of hash table operations?", "hard", ["O(n)", "all collide", "degenerate chain"]),
    ]),
    g("DSA_RECURSION_01", "DSA", "technical", [
        ("What is recursion and what two components must a recursive function have?", "easy", ["base case", "recursive call", "self invocation"]),
        ("What is a base case and why is it required to prevent infinite recursion?", "easy", ["termination condition", "stack overflow", "stop recursion"]),
        ("What is the time complexity of recursive factorial of n?", "medium", ["O(n)", "n calls", "linear recursion"]),
        ("What is tail recursion and how can some languages optimize it?", "medium", ["recursive call last", "tail call optimization", "no new stack"]),
        ("What is the space complexity of naive recursive Fibonacci without memoization?", "hard", ["O(n) stack", "exponential time", "call tree depth"]),
    ]),
    g("DSA_RECURSION_02", "DSA", "technical", [
        ("How does memoization change Fibonacci time complexity from exponential to linear?", "medium", ["cache results", "O(n)", "overlap subproblems"]),
        ("What is the difference between recursion and iteration for the same problem?", "medium", ["stack vs loop", "space tradeoff", "equivalent logic"]),
        ("What is divide and conquer and name two classic divide-and-conquer algorithms?", "medium", ["split solve combine", "merge sort quicksort", "subproblem independence"]),
        ("What is the master theorem used for?", "hard", ["recurrence solving", "asymptotic bounds", "divide conquer cost"]),
        ("When does recursion depth cause stack overflow on large inputs?", "hard", ["stack limit", "deep recursion", "iteration preferred"]),
    ]),
    g("DSA_DP_01", "DSA", "technical", [
        ("What is dynamic programming and what two properties enable it?", "easy", ["optimal substructure", "overlapping subproblems", "memo tabulation"]),
        ("What is the difference between memoization and tabulation?", "medium", ["top down bottom up", "cache vs table", "DP approaches"]),
        ("What is the 0/1 knapsack problem definition?", "medium", ["weight capacity", "maximize value", "one copy each"]),
        ("What is the time complexity of 0/1 knapsack DP with n items and capacity W?", "medium", ["O(nW)", "2D table", "pseudo polynomial"]),
        ("How do you reconstruct selected items after solving 0/1 knapsack DP?", "hard", ["backtrack table", "item inclusion", "DP trace"]),
    ]),
    g("DSA_DP_02", "DSA", "technical", [
        ("What is the longest increasing subsequence problem and a DP solution complexity?", "medium", ["O(n^2) DP", "subsequence order", "patience sorting O(n log n)"]),
        ("What is the edit distance (Levenshtein) between two strings?", "medium", ["insert delete replace", "min operations", "DP table"]),
        ("What is the time and space complexity of edit distance DP?", "medium", ["O(nm)", "2D DP", "string lengths"]),
        ("What is coin change minimum coins DP recurrence?", "medium", ["min over denominations", "unbounded coins", "DP array"]),
        ("What is the difference between 0/1 knapsack and unbounded knapsack DP?", "hard", ["one vs unlimited", "inner loop direction", "item reuse"]),
    ]),
    g("DSA_GREEDY_01", "DSA", "technical", [
        ("What is a greedy algorithm and what property justifies greedy choices?", "easy", ["local optimal", "greedy choice property", "no backtrack"]),
        ("What is the activity selection problem and its greedy strategy?", "medium", ["earliest finish", "max non-overlapping", "sorted by end"]),
        ("What is the greedy algorithm for fractional knapsack?", "medium", ["value per weight", "sort ratio", "O(n log n)"]),
        ("Why does greedy fail for 0/1 knapsack but work for fractional?", "hard", ["indivisible items", "counterexample", "fractional divisible"]),
        ("What is Huffman coding and what does it minimize?", "medium", ["prefix code", "expected length", "min heap build"]),
    ]),
    g("DSA_GREEDY_02", "DSA", "technical", [
        ("How does the greedy minimum spanning tree Kruskal algorithm work?", "medium", ["sort edges", "union find", "avoid cycles"]),
        ("How does Prim's MST algorithm differ from Kruskal's?", "medium", ["grow from vertex", "priority queue", "edge vs vertex greedy"]),
        ("What is the time complexity of Kruskal MST with union-find?", "medium", ["O(E log E)", "sort edges", "near linear UF"]),
        ("What is the greedy coloring of graphs and is it optimal?", "hard", ["not optimal chromatic", "vertex order", "upper bound"]),
        ("When must you prove greedy correctness versus using DP?", "hard", ["exchange argument", "greedy proof", "problem structure"]),
    ]),
    g("DSA_BACKTRACK_01", "DSA", "technical", [
        ("What is backtracking and how does it explore a search tree?", "easy", ["try undo", "decision tree", "prune invalid"]),
        ("How does backtracking solve the N-Queens problem?", "medium", ["column row checks", "place queen", "prune conflicts"]),
        ("What is constraint propagation in backtracking search?", "medium", ["prune early", "valid partial", "reduce branches"]),
        ("What is the time complexity of brute backtracking for N-Queens?", "hard", ["exponential", "factorial growth", "pruning helps"]),
        ("How does Sudoku solving use backtracking with pruning?", "medium", ["cell try digits", "constraint check", "undo on fail"]),
    ]),
]

ML_GROUPS = [
    g("ML_REGRESSION_01", "ML", "technical", [
        ("What is supervised learning regression and what is the target variable type?", "easy", ["continuous output", "real valued", "labeled pairs"]),
        ("What is linear regression and what loss does ordinary least squares minimize?", "easy", ["sum squared error", "linear hypothesis", "MSE"]),
        ("What is the closed-form normal equation solution for linear regression?", "medium", ["matrix inverse", "w equals XTX inverse XTy", "analytical"]),
        ("What is ridge regression and what hyperparameter penalizes large weights?", "medium", ["L2 penalty", "lambda", "weight shrinkage"]),
        ("What is the difference between ridge (L2) and lasso (L1) regularization effects on weights?", "hard", ["sparse lasso", "L2 shrinkage", "feature selection"]),
    ]),
    g("ML_REGRESSION_02", "ML", "technical", [
        ("What is polynomial regression and why is it still linear in parameters?", "medium", ["feature expansion", "linear in weights", "nonlinear curve"]),
        ("What is bias-variance tradeoff in regression models?", "medium", ["underfit overfit", "model complexity", "generalization"]),
        ("What metric is RMSE and how does it differ from MAE?", "medium", ["squared root mean", "absolute error", "outlier sensitivity"]),
        ("What is R-squared and what does it measure in regression?", "medium", ["explained variance", "1 minus residual ratio", "goodness fit"]),
        ("When does high R-squared still indicate a poor regression model?", "hard", ["overfitting", "nonlinear missed", "extrapolation failure"]),
    ]),
    g("ML_CLASSIFICATION_01", "ML", "technical", [
        ("What is binary classification and what does the model output represent?", "easy", ["two classes", "probability or label", "decision boundary"]),
        ("What is logistic regression and what function maps linear output to probability?", "easy", ["sigmoid", "log odds", "binary probabilistic"]),
        ("What is the log loss (cross-entropy) used for logistic regression?", "medium", ["negative log likelihood", "penalize wrong confident", "convex loss"]),
        ("What is a confusion matrix and what are precision and recall?", "medium", ["TP FP FN", "precision recall", "classification metrics"]),
        ("What is the F1 score and when is it preferred over accuracy?", "hard", ["harmonic mean", "imbalanced classes", "precision recall balance"]),
    ]),
    g("ML_CLASSIFICATION_02", "ML", "technical", [
        ("What is the softmax function in multi-class classification?", "medium", ["multiclass probabilities", "normalize exponentials", "mutually exclusive"]),
        ("What is one-vs-rest strategy for multi-class with binary classifiers?", "medium", ["K binary models", "one class positive", "multiclass decomposition"]),
        ("What is the ROC curve and what does AUC represent?", "medium", ["TPR vs FPR", "threshold sweep", "ranking quality"]),
        ("What is a support vector machine and what is the maximum margin principle?", "medium", ["max margin hyperplane", "support vectors", "separating boundary"]),
        ("What is the kernel trick in SVM and why is it used?", "hard", ["implicit feature map", "nonlinear boundary", "dot product space"]),
    ]),
    g("ML_CLASSIFICATION_03", "ML", "technical", [
        ("What is k-nearest neighbors classification and how does k affect the boundary?", "medium", ["distance vote", "k parameter", "local decision"]),
        ("What is decision tree splitting criterion using Gini impurity?", "medium", ["class purity", "Gini index", "split quality"]),
        ("What is information gain and how does ID3 use entropy?", "medium", ["entropy reduction", "ID3 C45", "tree split"]),
        ("What is random forest and how does bagging reduce variance?", "medium", ["ensemble trees", "bootstrap samples", "variance reduction"]),
        ("What is gradient boosting and how does it differ from random forest?", "hard", ["sequential correction", "residual fitting", "boosting vs bagging"]),
    ]),
    g("ML_CLUSTERING_01", "ML", "technical", [
        ("What is unsupervised clustering and what is the input without labels?", "easy", ["unlabeled data", "group similarity", "no target"]),
        ("What is k-means clustering objective function?", "easy", ["minimize within cluster sum squares", "centroid assignment", "WCSS"]),
        ("What are the steps of the k-means algorithm?", "medium", ["assign update centroids", "iterate until stable", "Lloyd algorithm"]),
        ("What is the elbow method for choosing k in k-means?", "medium", ["WCSS plot", "k elbow", "diminishing gain"]),
        ("Why is k-means sensitive to initialization and scale of features?", "hard", ["random centroids", "feature scaling", "local minima"]),
    ]),
    g("ML_CLUSTERING_02", "ML", "technical", [
        ("What is hierarchical agglomerative clustering?", "medium", ["merge clusters", "dendrogram", "linkage criteria"]),
        ("What is DBSCAN and how does it find clusters of arbitrary shape?", "medium", ["density reachable", "eps minPts", "noise points"]),
        ("What is silhouette score for cluster quality?", "medium", ["cohesion separation", "cluster validity", "average silhouette"]),
        ("What linkage criteria exist for hierarchical clustering (single, complete, average)?", "hard", ["linkage distance", "cluster merge rule", "dendrogram shape"]),
        ("When would you choose DBSCAN over k-means?", "hard", ["non spherical", "varying density", "noise outliers"]),
    ]),
    g("ML_FEATURE_01", "ML", "technical", [
        ("What is feature scaling and why is it important for distance-based models?", "easy", ["normalize standardize", "equal magnitude", "distance fairness"]),
        ("What is min-max normalization formula?", "easy", ["scale to 0 1", "min max range", "linear transform"]),
        ("What is standardization (z-score) and when is it preferred?", "medium", ["mean zero std one", "Gaussian assumption", "outlier effect"]),
        ("What is one-hot encoding for categorical variables?", "medium", ["binary columns per category", "no ordinal assumption", "sparse expansion"]),
        ("What is target encoding and what leakage risk does it carry?", "hard", ["mean target per category", "data leakage", "cross fold encoding"]),
    ]),
    g("ML_FEATURE_02", "ML", "technical", [
        ("What is principal component analysis (PCA) and what does it maximize?", "medium", ["variance projection", "orthogonal axes", "dimensionality reduction"]),
        ("What is feature selection versus feature extraction?", "medium", ["subset original", "transformed features", "dimension reduction"]),
        ("What is a polynomial feature and why can it cause overfitting?", "medium", ["interaction terms", "degree expansion", "high variance"]),
        ("What is missing value imputation with mean versus median?", "medium", ["central tendency", "outlier robust median", "imputation choice"]),
        ("What is the curse of dimensionality in machine learning?", "hard", ["distance concentration", "sparse high dim", "sample efficiency"]),
    ]),
    g("ML_EVAL_01", "ML", "technical", [
        ("What is train-validation-test split purpose?", "easy", ["fit tune evaluate", "generalization estimate", "data partition"]),
        ("What is k-fold cross-validation?", "medium", ["k partitions rotate", "robust estimate", "variance reduction"]),
        ("What is overfitting and how does validation loss detect it?", "medium", ["train low val high", "memorization", "generalization gap"]),
        ("What is early stopping during neural network training?", "medium", ["monitor val loss", "stop before overfit", "patience epochs"]),
        ("What is data leakage and give one example?", "hard", ["test info in train", "target leakage", "invalid evaluation"]),
    ]),
    g("ML_EVAL_02", "ML", "technical", [
        ("What is stratified k-fold for imbalanced classification?", "medium", ["preserve class ratio", "each fold balanced", "stratified split"]),
        ("What is a learning curve and what patterns indicate high bias or variance?", "medium", ["train val vs size", "bias underfit", "variance overfit"]),
        ("What is nested cross-validation for hyperparameter tuning?", "hard", ["inner outer loops", "unbiased performance", "tuning evaluation"]),
        ("What is calibration of predicted probabilities?", "medium", ["predicted vs observed", "reliability diagram", "probability accuracy"]),
        ("What is the difference between macro and micro averaged F1?", "hard", ["per class vs global", "multiclass averaging", "imbalance effect"]),
    ]),
    g("ML_NN_01", "ML", "technical", [
        ("What is a perceptron and what is its activation function classically?", "easy", ["linear threshold", "single layer", "binary output"]),
        ("What is an artificial neuron with weighted sum and activation?", "easy", ["weights bias activation", "nonlinear transform", "neuron model"]),
        ("What is backpropagation and what rule updates weights?", "medium", ["chain rule gradients", "gradient descent", "error propagation"]),
        ("What is the vanishing gradient problem in deep networks?", "medium", ["small gradients deep", "sigmoid saturation", "slow learning"]),
        ("What activation functions help mitigate vanishing gradients?", "medium", ["ReLU Leaky ReLU", "non saturating", "gradient flow"]),
    ]),
    g("ML_NN_02", "ML", "technical", [
        ("What is a feedforward neural network layer stacking?", "medium", ["fully connected layers", "depth width", "MLP"]),
        ("What is batch normalization and what does it normalize?", "medium", ["mini-batch mean std", "internal covariate shift", "trainable scale"]),
        ("What is dropout regularization during training?", "medium", ["random neuron drop", "ensemble effect", "overfitting reduction"]),
        ("What is the Xavier and He weight initialization purpose?", "medium", ["variance preservation", "activation scale", "stable gradients"]),
        ("What is the difference between SGD, momentum, and Adam optimizers?", "hard", ["adaptive learning", "momentum velocity", "Adam moments"]),
    ]),
    g("ML_NN_03", "ML", "technical", [
        ("What is the universal approximation theorem for neural networks?", "hard", ["single hidden layer", "sufficient neurons", "continuous functions"]),
        ("What is weight decay equivalent to in optimization?", "medium", ["L2 regularization", "penalize weights", "lambda term"]),
        ("What is gradient clipping and when is it used?", "medium", ["cap gradient norm", "RNN stability", "exploding gradients"]),
        ("What is a dead ReLU neuron and how can it occur?", "hard", ["always zero output", "large negative bias", "no gradient"]),
        ("What is transfer learning in neural networks?", "medium", ["pretrained weights", "fine tune head", "feature reuse"]),
    ]),
    g("ML_CNN_01", "ML", "technical", [
        ("What is a convolutional layer and what does a filter learn?", "easy", ["local receptive field", "kernel weights", "spatial patterns"]),
        ("What are padding and stride in convolution?", "medium", ["output size control", "stride step", "same valid padding"]),
        ("What is a pooling layer purpose in CNNs?", "medium", ["downsample spatial", "max average pool", "translation tolerance"]),
        ("Why do CNNs have fewer parameters than fully connected layers on images?", "medium", ["weight sharing", "local connectivity", "parameter efficiency"]),
        ("What is the typical architecture stack Conv Pool FC in image classifiers?", "medium", ["feature hierarchy", "spatial to vector", "classification head"]),
    ]),
    g("ML_CNN_02", "ML", "technical", [
        ("What is ResNet skip connection and what problem does it solve?", "medium", ["identity shortcut", "degradation depth", "gradient highway"]),
        ("What is 1x1 convolution used for?", "medium", ["channel mixing", "bottleneck", "dimension change"]),
        ("What is receptive field growth with stacked conv layers?", "medium", ["effective window", "stacked kernels", "spatial context"]),
        ("What is data augmentation for image training?", "medium", ["flip rotate crop", "synthetic diversity", "regularization"]),
        ("What is transfer learning with ImageNet pretrained CNN?", "medium", ["replace classifier", "fine tune layers", "feature extractor"]),
    ]),
    g("ML_RNN_01", "ML", "technical", [
        ("What is a recurrent neural network and what memory does it maintain?", "easy", ["hidden state", "sequential input", "temporal dependency"]),
        ("What is the vanishing gradient problem in vanilla RNN?", "medium", ["long sequences", "BPTT decay", "LSTM GRU fix"]),
        ("What is LSTM and what are cell state and gates?", "medium", ["forget input output gates", "cell state highway", "long memory"]),
        ("What is GRU compared to LSTM?", "medium", ["fewer gates", "update reset", "simpler RNN"]),
        ("What is bidirectional RNN and when is it used?", "medium", ["forward backward", "full context", "not generative"]),
    ]),
    g("ML_RNN_02", "ML", "technical", [
        ("What is sequence padding and masking in batch training?", "medium", ["variable length", "pad token mask", "ignore padded"]),
        ("What is teacher forcing in sequence training?", "medium", ["ground truth input", "training stability", "exposure bias"]),
        ("What is beam search in sequence decoding?", "medium", ["top k hypotheses", "sequence generation", "wider search"]),
        ("What is the BLEU score used to evaluate?", "medium", ["n-gram precision", "translation quality", "reference compare"]),
        ("What is attention mechanism purpose in seq2seq?", "hard", ["context vector dynamic", "decoder focus", "long sequence"]),
    ]),
    g("ML_TRANSFORMER_01", "ML", "technical", [
        ("What is self-attention and what are query key value?", "medium", ["scaled dot product", "Q K V matrices", "attention weights"]),
        ("What is multi-head attention benefit?", "medium", ["parallel heads", "multiple relations", "representation subspaces"]),
        ("What is positional encoding in transformers and why needed?", "medium", ["order information", "sin cos encoding", "no recurrence"]),
        ("What is the transformer encoder layer components?", "medium", ["self attention FFN", "residual norm", "stack layers"]),
        ("What is computational complexity of self-attention with sequence length n?", "hard", ["O(n^2)", "quadratic pairs", "long sequence cost"]),
    ]),
    g("ML_TRANSFORMER_02", "ML", "technical", [
        ("What is masked self-attention in decoder for autoregressive models?", "medium", ["causal mask", "no peek future", "GPT style"]),
        ("What is BERT pretraining objective masked language modeling?", "medium", ["predict masked tokens", "bidirectional encoder", "MLM"]),
        ("What is GPT autoregressive language modeling objective?", "medium", ["next token prediction", "causal LM", "left to right"]),
        ("What is fine-tuning versus zero-shot with pretrained transformers?", "medium", ["task specific head", "no task training", "prompt inference"]),
        ("What is layer normalization placement in transformer blocks?", "hard", ["pre-norm post-norm", "training stability", "architecture variant"]),
    ]),
    g("ML_DEPLOY_01", "ML", "technical", [
        ("What is model serialization and why save weights separately from architecture?", "easy", ["pickle onnx", "weights config", "deployment artifact"]),
        ("What is batch inference versus online real-time inference?", "medium", ["throughput latency", "batching tradeoff", "serving mode"]),
        ("What is model drift and data drift in production?", "medium", ["distribution shift", "performance degrade", "monitoring trigger"]),
        ("What is A/B testing for model deployment?", "medium", ["champion challenger", "statistical comparison", "safe rollout"]),
        ("What is ONNX format purpose in ML deployment?", "medium", ["interoperability", "runtime optimize", "cross framework"]),
    ]),
    g("ML_DEPLOY_02", "ML", "technical", [
        ("What is feature store in ML systems?", "medium", ["consistent features", "train serve parity", "centralized features"]),
        ("What is shadow deployment for new models?", "medium", ["parallel predict no serve", "risk free eval", "production traffic"]),
        ("What is latency SLA impact of model size on serving?", "medium", ["inference time", "model compression", "edge deploy"]),
        ("What techniques reduce model size for deployment (quantization pruning)?", "hard", ["INT8 quantize", "prune weights", "distillation"]),
        ("What is CI/CD for ML (MLOps) pipeline stages?", "hard", ["train validate deploy monitor", "automated pipeline", "retrain trigger"]),
    ]),
]

AI_GROUPS = [
    g("AI_SEARCH_01", "AI", "technical", [
        ("What is uninformed search in AI and name two algorithms?", "easy", ["no heuristic", "BFS DFS", "blind search"]),
        ("What is BFS completeness and optimality on finite graphs?", "medium", ["complete finite", "optimal unit cost", "layer expansion"]),
        ("What is DFS memory advantage versus BFS?", "medium", ["O(depth) space", "stack storage", "memory tradeoff"]),
        ("What is iterative deepening DFS and why combine DFS and BFS benefits?", "medium", ["depth limited repeat", "linear space", "optimal complete"]),
        ("What is the branching factor role in search complexity?", "hard", ["exponential growth", "b factor", "search tree size"]),
    ]),
    g("AI_SEARCH_02", "AI", "technical", [
        ("What is a heuristic function in informed search?", "easy", ["estimate to goal", "h(n)", "guided search"]),
        ("What is admissibility of a heuristic for A*?", "medium", ["never overestimate", "h <= actual", "optimality condition"]),
        ("What is consistency (monotonicity) of heuristics?", "medium", ["h(n) <= cost(n,n')+h(n')", "triangle heuristic", "A* efficiency"]),
        ("What is A* search combining what two costs?", "medium", ["g plus h", "best first", "optimal admissible"]),
        ("What is greedy best-first search and is it optimal?", "hard", ["h only", "not optimal", "fast heuristic"]),
    ]),
    g("AI_KR_01", "AI", "technical", [
        ("What is knowledge representation in AI?", "easy", ["symbolic facts", "ontology", "machine readable"]),
        ("What is propositional logic and what are atoms and connectives?", "easy", ["true false", "AND OR NOT", "boolean logic"]),
        ("What is first-order logic extension over propositional logic?", "medium", ["quantifiers predicates", "variables domains", "FOL"]),
        ("What is forward chaining in rule-based inference?", "medium", ["data driven", "apply rules", "modus ponens"]),
        ("What is backward chaining goal-driven inference?", "medium", ["prove goal", "subgoal decomposition", "goal driven"]),
    ]),
    g("AI_KR_02", "AI", "technical", [
        ("What is a semantic network in knowledge representation?", "medium", ["nodes relations", "graph knowledge", "inheritance"]),
        ("What is description logic used for?", "medium", ["ontology formal", "TBox ABox", "structured concepts"]),
        ("What is frame problem in AI reasoning?", "hard", ["what not changes", "action effects", "reasoning efficiency"]),
        ("What is closed world versus open world assumption?", "hard", ["unknown false", "unknown possible", "knowledge assumption"]),
        ("What is ontological commitment in KR choice?", "hard", ["what exists modeled", "representation choice", "semantic scope"]),
    ]),
    g("AI_EXPERT_01", "AI", "technical", [
        ("What is an expert system architecture components?", "easy", ["knowledge base", "inference engine", "user interface"]),
        ("What is a production rule in expert systems?", "medium", ["if then rules", "condition action", "rule base"]),
        ("What is certainty factor in MYCIN style reasoning?", "medium", ["uncertainty numeric", "combine beliefs", "non probabilistic"]),
        ("What is knowledge engineering elicitation process?", "medium", ["expert interviews", "rule extraction", "domain modeling"]),
        ("What limits expert systems compared to modern ML?", "hard", ["brittle rules", "maintenance cost", "scaling knowledge"]),
    ]),
    g("AI_RL_01", "AI", "technical", [
        ("What is reinforcement learning agent environment interaction?", "easy", ["state action reward", "trial feedback", "no labeled data"]),
        ("What is the Markov decision process tuple components?", "medium", ["S A P R gamma", "MDP formalism", "transition reward"]),
        ("What is the discount factor gamma purpose?", "medium", ["future reward weight", "0 to 1", "finite horizon"]),
        ("What is policy in RL and value function V versus Q?", "medium", ["action mapping", "state value", "state action value"]),
        ("What is exploration versus exploitation tradeoff?", "hard", ["try new vs best", "epsilon greedy", "bandit problem"]),
    ]),
    g("AI_RL_02", "AI", "technical", [
        ("What is Q-learning update rule type (off-policy)?", "medium", ["TD target max Q", "off policy", "tabular Q"]),
        ("What is SARSA on-policy TD control?", "medium", ["actual next action", "on policy", "TD control"]),
        ("What is policy gradient REINFORCE idea?", "medium", ["gradient ascent return", "direct policy optimize", "Monte Carlo policy"]),
        ("What is deep Q-network experience replay purpose?", "medium", ["break correlation", "replay buffer", "stable training"]),
        ("What is actor-critic architecture combining?", "hard", ["policy and value", "advantage estimate", "A2C A3C"]),
    ]),
    g("AI_NLP_01", "AI", "technical", [
        ("What is natural language processing scope?", "easy", ["text understanding", "generation translation", "human language"]),
        ("What is tokenization in NLP pipeline?", "easy", ["split text tokens", "word subword", "preprocessing"]),
        ("What is Word2Vec skip-gram training objective?", "medium", ["predict context", "embedding learn", "CBOW contrast"]),
        ("What is attention in transformers replacing in seq2seq?", "medium", ["fixed context vector", "dynamic alignment", "encoder decoder"]),
        ("What is BERT versus GPT architecture difference?", "hard", ["encoder bidirectional", "decoder causal", "pretraining objective"]),
    ]),
    g("AI_NLP_02", "AI", "technical", [
        ("What is named entity recognition task?", "medium", ["span classification", "person org loc", "sequence labeling"]),
        ("What is part-of-speech tagging?", "medium", ["word category", "syntax label", "sequence tag"]),
        ("What is sentiment analysis classification output?", "medium", ["positive negative", "opinion polarity", "text classification"]),
        ("What is BLEU metric limitation for NLG evaluation?", "medium", ["n-gram overlap", "no semantics", "reference required"]),
        ("What is perplexity metric for language models?", "hard", ["exp cross entropy", "LM quality", "lower better"]),
    ]),
    g("AI_NLP_03", "AI", "technical", [
        ("What is TF-IDF weighting formula components?", "medium", ["term frequency", "inverse document frequency", "sparse vector"]),
        ("What is subword tokenization BPE advantage?", "medium", ["OOV reduction", "merge frequent pairs", "compact vocab"]),
        ("What is zero-shot classification with LLM prompts?", "medium", ["no task training", "instruction prompt", "label in text"]),
        ("What is RAG retrieval augmented generation?", "hard", ["retrieve documents", "augment context", "reduce hallucination"]),
        ("What is hallucination in LLM outputs?", "hard", ["false confident facts", "not grounded", "generation risk"]),
    ]),
    g("AI_CV_01", "AI", "technical", [
        ("What is computer vision field focus?", "easy", ["image video理解", "visual input", "pixel data"]),
        ("What is image classification task definition?", "easy", ["single label image", "category assign", "whole image"]),
        ("What is object detection versus image classification?", "medium", ["bounding boxes", "localize and classify", "multiple objects"]),
        ("What is IoU metric in object detection evaluation?", "medium", ["intersection union", "box overlap", "detection match"]),
        ("What is non-max suppression purpose in detection?", "medium", ["duplicate box remove", "overlap suppress", "NMS threshold"]),
    ]),
    g("AI_CV_02", "AI", "technical", [
        ("What is semantic segmentation output type?", "medium", ["per pixel class", "dense label map", "segment regions"]),
        ("What is CNN feature hierarchy from low to high level?", "medium", ["edges textures objects", "hierarchical features", "deep layers"]),
        ("What is data augmentation for vision robustness?", "medium", ["geometric color jitter", "train diversity", "generalization"]),
        ("What is YOLO single-shot detection idea?", "hard", ["grid predict boxes", "one forward pass", "real-time detect"]),
        ("What is transfer learning on limited image data?", "hard", ["pretrained backbone", "fine tune head", "small dataset"]),
    ]),
]

BEHAVIORAL_GROUPS = [
    g("BEH_OWNERSHIP_01", "behavioral", "behavioral", [
        ("Describe a situation where you took responsibility for a bug in production. What steps did you take?", "easy", ["root cause", "fix deploy", "accountability"]),
        ("How do you prioritize tasks when multiple urgent issues arrive at the same time?", "medium", ["impact assess", "communicate stakeholders", "priority order"]),
        ("What metrics or signals do you use to verify a production fix resolved the issue?", "medium", ["monitoring logs", "error rate", "verification"]),
        ("How do you document incident resolution for future team reference?", "medium", ["postmortem", "runbook update", "knowledge share"]),
        ("What is the difference between a hotfix and a proper long-term solution after an incident?", "hard", ["temporary patch", "technical debt", "sustainable fix"]),
    ]),
    g("BEH_OWNERSHIP_02", "behavioral", "behavioral", [
        ("How do you handle a task when requirements are unclear at the start?", "easy", ["clarify questions", "assumptions document", "stakeholder align"]),
        ("What do you do when you realize you cannot meet a committed deadline?", "medium", ["early communicate", "scope negotiate", "risk escalate"]),
        ("How do you track progress on a multi-week feature you own?", "medium", ["milestones", "status updates", "blocker tracking"]),
        ("How do you balance speed and code quality under deadline pressure?", "medium", ["minimum viable", "test coverage", "tradeoff conscious"]),
        ("What steps do you take before handing off a feature you built to another engineer?", "hard", ["documentation", "code walkthrough", "support period"]),
    ]),
    g("BEH_TEAM_01", "behavioral", "behavioral", [
        ("How do you approach code review feedback that you disagree with?", "easy", ["open discussion", "evidence rationale", "respectful"]),
        ("Describe how you coordinate with teammates on a shared codebase.", "medium", ["branch strategy", "communication", "merge conflicts"]),
        ("How do you onboard a new team member to a project codebase?", "medium", ["pairing", "docs pointers", "gradual tasks"]),
        ("What practices reduce integration issues in team development?", "medium", ["CI tests", "small PRs", "continuous integration"]),
        ("How do you handle a teammate whose code repeatedly introduces bugs?", "hard", ["constructive feedback", "pair programming", "process improve"]),
    ]),
    g("BEH_TEAM_02", "behavioral", "behavioral", [
        ("How do you share knowledge after solving a difficult technical problem?", "easy", ["wiki doc", "team demo", "write up"]),
        ("What do you do when two team members disagree on a technical approach?", "medium", ["facilitate discussion", "criteria decide", "prototype compare"]),
        ("How do you ensure your work does not block other engineers?", "medium", ["interface contracts", "early integration", "dependency communicate"]),
        ("How do you participate in sprint planning as an engineer?", "medium", ["estimate tasks", "identify risks", "capacity honest"]),
        ("What is your approach to remote/async collaboration with a distributed team?", "hard", ["written updates", "timezone respect", "clear ownership"]),
    ]),
    g("BEH_DEBUG_01", "behavioral", "behavioral", [
        ("What is your first step when a test fails unexpectedly in CI?", "easy", ["reproduce locally", "read error log", "isolate change"]),
        ("How do you narrow down the root cause of an intermittent bug?", "medium", ["logging reproduce", "bisect commits", "hypothesis test"]),
        ("What tools do you use to debug a performance regression?", "medium", ["profiler", "metrics compare", "benchmark"]),
        ("How do you debug a issue that only occurs in production?", "hard", ["production logs", "feature flags", "safe reproduce"]),
        ("What information do you include in a bug report for efficient resolution?", "hard", ["steps reproduce", "expected actual", "environment version"]),
    ]),
    g("BEH_DEBUG_02", "behavioral", "behavioral", [
        ("How do you use breakpoints and logging differently when debugging?", "easy", ["interactive state", "persistent trace", "tool choice"]),
        ("Describe your approach to debugging a failing API endpoint.", "medium", ["request response", "status codes", "layer isolate"]),
        ("How do you verify a fix does not introduce regressions?", "medium", ["regression tests", "related suites", "manual smoke"]),
        ("What is your process after finding the root cause of a critical bug?", "medium", ["fix test deploy", "monitor verify", "communicate status"]),
        ("How do you debug memory or resource leaks in an application?", "hard", ["heap dump", "leak detector", "resource lifecycle"]),
    ]),
    g("BEH_COMM_01", "behavioral", "behavioral", [
        ("How do you explain a technical concept to a non-technical stakeholder?", "easy", ["simple language", "analogy", "avoid jargon"]),
        ("What structure do you use when writing a technical design document?", "medium", ["problem solution", "tradeoffs", "diagrams"]),
        ("How do you communicate project status in a weekly update?", "medium", ["progress blockers", "next steps", "concise"]),
        ("How do you ask for help when stuck on a problem?", "medium", ["specific question", "context provided", "time boxed"]),
        ("How do you handle receiving critical feedback on your work?", "hard", ["listen reflect", "action plan", "no defensive"]),
    ]),
    g("BEH_COMM_02", "behavioral", "behavioral", [
        ("How do you document API changes for consumers?", "easy", ["changelog", "version notes", "breaking highlight"]),
        ("What do you include in a pull request description?", "medium", ["why change", "how test", "screenshots logs"]),
        ("How do you run an effective technical discussion meeting?", "medium", ["agenda", "time box", "decision record"]),
        ("How do you communicate technical risk before a release?", "medium", ["risk register", "rollback plan", "stakeholder align"]),
        ("What is your approach to writing clear error messages for users?", "hard", ["actionable text", "error codes", "user context"]),
    ]),
    g("BEH_LEARN_01", "behavioral", "behavioral", [
        ("How do you learn a new programming language or framework for a project?", "easy", ["official docs", "small prototype", "incremental"]),
        ("What resources do you use to stay updated with software engineering practices?", "medium", ["blogs courses", "conferences", "peer learning"]),
        ("How do you evaluate whether a new technology is worth adopting?", "medium", ["proof of concept", "team fit", "maintenance cost"]),
        ("How do you recover learning momentum after struggling with a hard topic?", "medium", ["break down topic", "practice exercises", "mentor ask"]),
        ("What is your process for reviewing and retaining what you learned?", "hard", ["notes summarize", "teach others", "apply project"]),
    ]),
    g("BEH_CONFLICT_01", "behavioral", "behavioral", [
        ("How do you respond when a code review comment feels overly critical?", "easy", ["assume good intent", "clarify ask", "professional"]),
        ("Describe how you resolved a disagreement about technical direction.", "medium", ["data driven", "prototype", "consensus build"]),
        ("What do you do when product and engineering priorities conflict?", "medium", ["tradeoff discuss", "scope negotiate", "stakeholder align"]),
        ("How do you handle conflict when you believe your approach is correct?", "medium", ["evidence present", "listen other view", "escalate if needed"]),
        ("What steps prevent recurring conflicts on the same technical decisions?", "hard", ["ADR document", "team standards", "architecture review"]),
    ]),
]

# Fix AI_CV_01 - remove accidental Chinese character
for grp in AI_GROUPS:
    for q in grp["questions"]:
        q["text"] = q["text"].replace("理解", "understanding")


def all_groups():
    return DSA_GROUPS + ML_GROUPS + AI_GROUPS + BEHAVIORAL_GROUPS


def escape_sql(text: str) -> str:
    return text.replace("'", "''")


def build_sql() -> str:
    groups = all_groups()
    total_q = sum(len(g["questions"]) for g in groups)
    expected = len(groups) * QUESTIONS_PER_GROUP
    if total_q != expected:
        raise ValueError(f"Expected {expected} questions, got {total_q}")

    lines = [
        "INSERT INTO questions",
        "(question_id, question_text, category, difficulty, topics, job_roles, embedding, ideal_keywords,",
        " question_group, followup_order, parent_question_id, created_at, updated_at)",
        "VALUES",
        "",
    ]

    qnum = 0
    for grp in groups:
        parent_id = None
        for order, item in enumerate(grp["questions"], start=1):
            qnum += 1
            qid = f"Q{qnum:03d}"
            if order == 1:
                parent_id = qid
                parent_sql = "NULL"
            else:
                parent_sql = f"'{parent_id}'"

            topics_json = escape_sql(json.dumps([grp["topic"]]))
            roles_json = escape_sql(json.dumps(ROLE))
            kw_json = escape_sql(json.dumps(item["kw"]))
            text = escape_sql(item["text"])

            row = (
                f"('{qid}','{text}','{grp['category']}','{item['diff']}',"
                f"'{topics_json}','{roles_json}','[]','{kw_json}',"
                f"'{grp['id']}',{order},{parent_sql},'{TODAY}','{TODAY}')"
            )
            lines.append(row + ("," if qnum < total_q else ";"))

    return "\n".join(lines)


def main():
    sql = build_sql()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(sql, encoding="utf-8")
    groups = all_groups()
    print(f"Generated {sum(len(g['questions']) for g in groups)} questions in {len(groups)} groups")
    print(f"Written to {OUTPUT}")


if __name__ == "__main__":
    main()
