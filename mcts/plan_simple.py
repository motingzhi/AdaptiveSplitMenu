

import utility
import sys
import argparse
from useroracle import UserStrategy, UserOracle
import state
import useroracle
import mcts
from state import State, MenuState, UserState
from copy import deepcopy

# Setup command-line arguments and options
parser = argparse.ArgumentParser()
parser.add_argument("--menu", "-m", help="Input menu name", default="menu_5items.txt")
parser.add_argument("--history", "-H", help="Click frequency file name", default="history_5items.csv")
parser.add_argument("--associations", "-a", help="Association list file name", default="associations_5items.txt")
parser.add_argument("--strategy", "-s", help="User search strategy", default="average",
                    choices=["serial", "forage", "recall", "average"])
parser.add_argument("--time", "-t", type=int, help="time budget", default=3000)
parser.add_argument("--iterations", "-i", type=int, help="num iterations", default=200)
parser.add_argument("--depth", "-d", type=int, help="maximum depth", default=5)
parser.add_argument("--case", "-c", help="Use case e.g. 5items, 10items, toy (combination of menu, assoc, history)")
parser.add_argument("--objective", "-O", help="Objective to use", choices=["average", "optimistic", "conservative"],
                    default="average")

args = parser.parse_args()

vn_name: "a"
use_network = False

# Objective function to be used; default is average
objective = args.objective.upper()
# objective = "AVERAGE" 新加的
# Set-up the menu instance
currentmenu = utility.load_menu("./input/" + args.menu)  # load menu items from text file
print("currentmenu is",currentmenu)
freqdist, total_clicks, history = utility.load_click_distribution(currentmenu,
                                                                  "./input/" + args.history)  # load from user history (CSV file)
associations = utility.load_associations(currentmenu,
                                         "./input/" + args.associations)  # load assocation matrix from text file
# assoc_test = utility.compute_associations(currentmenu) # Experimental: word-embedding models for associations

# If --case is included in CLI arguments
if args.case is not None:
    print(args.case)
    currentmenu = utility.load_menu("./input/menu_" + args.case + ".txt")
    freqdist, total_clicks, history = utility.load_click_distribution(currentmenu,
                                                                      "./input/history_" + args.case + ".csv")
    associations = utility.load_associations(currentmenu, "./input/associations_" + args.case + ".txt")
    vn_name = "value_network_" + args.case + ".h5"

# If different objective function is specified
strategy = UserStrategy.AVERAGE
if args.strategy == "serial":
    strategy = UserStrategy.SERIAL
elif args.strategy == "forage":
    strategy = UserStrategy.FORAGE
elif args.strategy == "recall":
    strategy = UserStrategy.RECALL

# MCTS search parameters
maxdepth = args.depth
print("maxdepth",maxdepth)
timebudget = args.time
iteration_limit = args.iterations

weights = [0.25, 0.5, 0.25]  # Weights for the 3 models

if strategy == UserStrategy.SERIAL:
    weights = [1.0, 0.0, 0.0]
elif strategy == UserStrategy.FORAGE:
    weights = [0.0, 1.0, 0.0]
elif strategy == UserStrategy.RECALL:
    weights = [0.0, 0.0, 1.0]

# Intialise the root state using the input menu, associations, and user history
menu_state = MenuState(currentmenu, associations)
user_state = UserState(freqdist, total_clicks, history)
root_state = State(menu_state, user_state, exposed=True)
my_oracle = UserOracle(maxdepth, associations=menu_state.associations)
completion_times = my_oracle.get_individual_rewards(root_state)[1]  # Initial completion time for current menu
avg_time = sum([a * b for a, b in zip(weights, completion_times)])

# Start the planner

print("Planning started. Strategy:", strategy)
print("Original menu: ", menu_state.simplified_menu(), avg_time)
print("Freq. dist:", freqdist)
print("Associations:", associations)


# Execute the MCTS planner and return sequence of adaptations
def step(state, oracle, weights, objective, use_network, network_name, timebudget):
    results = []
    original_times = oracle.get_individual_rewards(state)[1]
    print("xoriginal_times", original_times)
    tree = mcts.mcts(oracle, weights, objective, use_network, network_name, time_limit=timebudget)
    node = None

    while not oracle.is_terminal(state):
        _, best_child, _, _ = tree.search(state,
                                          node)  # search returns selected (best) adaptation, child state, avg rewards
        node = best_child
        state = best_child.state
        [rewards, times] = oracle.get_individual_rewards(state)
        print(state)
        print("22",rewards, times)
        print("44",times)
        if objective == "AVERAGE":
            avg_reward = sum([a * b for a, b in zip(weights, rewards)])  # Take average reward
            avg_time = sum([a * b for a, b in zip(weights, times)])

            avg_original_time = sum(
                [a * b for a, b in zip(weights, original_times)])  # average selection time for the original design
        elif objective == "OPTIMISTIC":
            avg_reward = max(rewards)  # Take best reward
            avg_time = min(times)
            avg_original_time = min(original_times)
        elif objective == "CONSERVATIVE":
            avg_reward = min(rewards)  # Take minimum; add penalty if negative
            avg_time = max(times)
            avg_original_time = max(original_times)

        # avg_reward = sum([a * b for a, b in zip(weights, rewards)])
        # avg_time = sum([a * b for a, b in zip(weights, times)])
        if avg_time > avg_original_time and state.exposed:
            exposed = False  # Heuristic. There must be a time improvement to show the menu
        else:
            exposed = state.exposed
        results.append(
            [state.menu_state.simplified_menu(), state.depth, exposed, round(avg_original_time, 2), round(avg_time, 2),
             round(avg_reward, 2)])
    return avg_reward, results


result = step(root_state, my_oracle, weights, objective, False, None, timebudget)
bestmenu = result[1]
# Get results and save output
for step in bestmenu:
    print(step)
    if step[2]:
        utility.save_menu(step[0], "output/adaptedmenu" + str(step[1]) + "1.txt")
        newmenu=step[0]
        print(newmenu)

##############Split part:
# class Newmenu():
#
#         def newmenu(self):
#             return newmenu


