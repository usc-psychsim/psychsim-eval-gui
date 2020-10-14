# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 14:35:40 2020

@author: mostafh
"""
import sys
print(sys.path)
sys.path.insert(1, "../../../atomic")
sys.path.insert(1, "../../../atomic_domain_definitions")

from psychsim.agent import ValueFunction
from psychsim.world import World, WORLD
from psychsim.pwl import stateKey, Distribution, actionKey, VectorDistributionSet, ActionSet
from new_locations import Locations, Directions
from victims import Victims
from SandRMap import getSandRMap, getSandRVictims, getSmallSandRMap, getSmallSandRVictims, checkSRMap
import pprint

pp = pprint.PrettyPrinter(indent=4)


def print_methods(obj):
    # useful for finding methods of an object
    obj = triageAgent
    object_methods = [method_name for method_name in dir(obj)
                      if callable(getattr(obj, method_name))]
    print(object_methods)


class GuiTestSim:
    def __init__(self):
        self.sim_steps = 50
        # MDP or POMDP
        Victims.FULL_OBS = True

        ##################
        ##### Get Map Data
        SandRLocs = getSmallSandRMap()
        SandRVics = getSmallSandRVictims()
        ##################

        self.world = World()
        k = self.world.defineState(WORLD, 'seconds', int)
        self.world.setFeature(k, 0)

        self.agents= ['TriageAg1', 'TriageAg2']
        #TODO: fix this to make it use the above variable (and check that it is uses the belle_fewacts setup)
        self.triageAgent = self.world.addAgent('TriageAg1')
        self.triageAgent2 = self.world.addAgent('TriageAg2')
        agent = self.world.addAgent('ATOMIC')

        VICTIMS_LOCS = list(SandRVics.keys())
        VICTIM_TYPES = [SandRVics[v] for v in VICTIMS_LOCS]
        Victims.world = self.world
        Victims.makeVictims(VICTIMS_LOCS, VICTIM_TYPES, [self.triageAgent.name, self.triageAgent2.name], list(SandRLocs.keys()))
        Victims.makePreTriageActions(self.triageAgent)
        Victims.makeTriageAction(self.triageAgent)
        Victims.makePreTriageActions(self.triageAgent2)
        Victims.makeTriageAction(self.triageAgent2)

        ## Create triage agent's observation variables related to victims
        if not Victims.FULL_OBS:
            Victims.makeVictimObservationVars(self.triageAgent)
            Victims.makeVictimObservationVars(self.triageAgent2)

        ################# Locations and Move actions
        Locations.EXPLORE_BONUS = 0
        Locations.world = self.world
        # Locations.makeMap([(0,1), (1,2), (1,3)])
        #  Locations.makeMap([])
        Locations.makeMapDict(SandRLocs)
        Locations.makePlayerLocation(self.triageAgent, "BH2")
        Locations.makePlayerLocation(self.triageAgent2, "BH1")

        ## These must come before setting triager's beliefs
        # self.world.setOrder([{self.triageAgent.name}, {self.triageAgent2.name}])
        self.world.setOrder([{self.triageAgent.name}])

        ## Set players horizons
        self.horizon = 4
        self.triageAgent.setAttribute('horizon', self.horizon)
        # self.triageAgent.setAttribute('selection', 'random')
        self.triageAgent2.setAttribute('horizon', 4)

        ## Set uncertain beliefs
        if not Victims.FULL_OBS:
            self.triageAgent.omega = {actionKey(self.triageAgent.name)}
            self.triageAgent.omega = self.triageAgent.omega.union({stateKey(self.triageAgent.name, obs) for obs in \
                                                         ['obs_victim_status', 'obs_victim_reward', 'obs_victim_danger']})
            Victims.beliefAboutVictims(self.triageAgent)


        ######################
        ## SETUP Simulation
        ######################
        print('Initial State')
        self.world.printBeliefs(self.triageAgent.name)


    def run_step(self):
        legalActions = self.triageAgent.getActions()
        agent_state = self.triageAgent.getState('loc')
        agent_belief = self.triageAgent.getBelief()
        print("Player state: ", agent_state)
        print("reward: ", self.triageAgent.reward())
        #  print(self.triageAgent.getAttribute('R',model='TriageAg10'))
        print('Legal Actions:')
        for a, n in zip(legalActions, range(len(legalActions))):
            print(n, ': ', a)
        print()
        print('Triage Agent Reward: ', self.triageAgent.reward())

        result0 = {'TriageAg1': {}}
        self.world.step(debug=result0)
        intermediate_results = result0['TriageAg1']

        print('Triage Agent Reward: ', self.triageAgent.reward())

        return_result = {"WORLD_STATE": self.world.state,
                         "AGENT_STATE": result0}
        return return_result


if __name__ == "__main__":
    sim = GuiTestSim()
    for step in range(10):
        sim.run_step()
