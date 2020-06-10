# -*- coding: utf-8 -*-

# import sys
# print(sys.path)
# psychsim_path = "../../atomic"
# definitions_path = "../../atomic_domain_definitions"
# sys.path.insert(1, psychsim_path)
# sys.path.insert(1, definitions_path)

from psychsim.agent import ValueFunction
from psychsim.world import World, WORLD
from psychsim.pwl import stateKey, Distribution, actionKey, VectorDistributionSet, ActionSet
from new_locations import Locations, Directions
from victims import Victims
from SandRMap import getSandRMap, getSandRVictims, getSmallSandRMap, getSmallSandRVictims, checkSRMap
import pprint

pp = pprint.PrettyPrinter(indent=4)

class GuiTestSimClean:
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

        self.triageAgent = self.world.addAgent('TriageAg1')
        agent = self.world.addAgent('ATOMIC')

        VICTIMS_LOCS = list(SandRVics.keys())
        VICTIM_TYPES = [SandRVics[v] for v in VICTIMS_LOCS]
        Victims.world = self.world
        Victims.makeVictims(VICTIMS_LOCS, VICTIM_TYPES, [self.triageAgent.name], list(SandRLocs.keys()))
        Victims.makePreTriageActions(self.triageAgent)
        Victims.makeTriageAction(self.triageAgent)

        ## Create triage agent's observation variables related to victims
        if not Victims.FULL_OBS:
            Victims.makeVictimObservationVars(self.triageAgent)

        ################# Locations and Move actions
        Locations.EXPLORE_BONUS = 0
        Locations.world = self.world
        # Locations.makeMap([(0,1), (1,2), (1,3)])
        #  Locations.makeMap([])
        Locations.makeMapDict(SandRLocs)
        Locations.makePlayerLocation(self.triageAgent, "BH2")

        ## These must come before setting triager's beliefs
        self.world.setOrder([{self.triageAgent.name}])

        ## Set players horizons
        self.horizon = 4
        self.triageAgent.setAttribute('horizon', self.horizon)
        self.triageAgent.setAttribute('selection', 'random')

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
        # get some info before the step
        result0 = {'TriageAg1': {}}
        # step the sim
        self.world.step(debug=result0)

        return_result = {"WORLD_STATE": self.world.state,
                         "AGENT_STATE": result0}
        return return_result


if __name__ == "__main__":
    sim = GuiTestSimClean()
    for step in range(10):
        print(step)
        result = sim.run_sim()
