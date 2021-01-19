
import pickle

file = open("output/benchmark/trajectories_pickle20210119-144324", 'rb')
trajectories = pickle.load(file)
file.close()

agent_name = 'Player'


from appraisal import appraisal_dimensions as ad

player_step_appraisal_info = {}
player_pre_utility = {}

step = 0
for t in trajectories[0]:
    player_appraisal = ad.PlayerAppraisal()

    traj_world = t[0]
    traj_agent = traj_world.agents[agent_name]
    traj_debug = t[2]

    if step == 0:
        # for key, model in traj_agent.modelList.items():
        player_pre_utility = traj_agent.getState("__REWARD__").domain()[0] # THIS DOESN"T SEEM TO UPDATE

    player_loc = player_loc_actual = traj_world.getFeature(f"{traj_agent.name}'s loc", traj_agent.world.state)

    print("=================")
    print(f"STEP: {step}")
    print(f"PRE UTILITY: {player_pre_utility}")
    print(f"PRE LOC: {player_loc}")

    loc = traj_world.getFeature(f"{agent_name}'s loc", traj_world.state)
    player_cur_utility = traj_agent.getState("__REWARD__").domain()[0]
    print(f"LOC: {loc}")
    legal_actions = traj_agent.getLegalActions()
    print(f"LEGAL ACTIONS: {legal_actions}")
    print(f"Action: {traj_agent.getState('__ACTION__').domain()[0]}")
    print(f"CUR UTILITY: {player_cur_utility}")

    # for model_name in ['Player0', 'prefer_green']:
        #TODO: make this actually work over each model - though only different models (i.e. statically added models, not all the newly generated ones...

    # player_cur_utility = player.getReward(m)# this is actually the reward function!!
    player_appraisal = ad.PlayerAppraisal()
    player_appraisal.motivational_relevance = ad.motivational_relevance(player_pre_utility,
                                                                        player_cur_utility)
    print(f"MOTIVATIONAL REL: {player_appraisal.motivational_relevance}")

    player_appraisal.motivational_congruence = ad.motivational_congruence(player_pre_utility,
                                                                          player_cur_utility)
    print(f"MOTIVATIONAL CONG: {player_appraisal.motivational_congruence}")
    # player_appraisal.novelty = #TODO: figure out what the possible actions are (legal?) and how to rank them
    # player_appraisal.accountable = ad.accountability(...) # TODO: figure out who should be the observer (maybe this doesn't work in single player?)
    # player_appraisal.control = #TODO: figure out how to do the projected action stuff
    player_step_appraisal_info[step] = player_appraisal

    player_pre_utility = player_cur_utility
    step = step + 1

pass