# -*- coding: utf-8 -*-

# import sys
# print(sys.path)
# psychsim_path = "/home/chris/Documents/GLASGOW_MARSELLA/atomic"
# definitions_path = "/home/chris/Documents/GLASGOW_MARSELLA/atomic_domain_definitions"
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

    def run_sim(self):
        # get some info before the step
        legalActions = self.triageAgent.getActions()
        agent_state = self.triageAgent.getState('loc')
        agent_belief = self.triageAgent.getBelief()
        result0 = {'TriageAg1': {}}

        # valuefn = ValueFunction()
        # valuefn.set("TriageAg1", self.triageAgent.world.state, "TriageAg1-move-E", self.horizon, 0)
        # predicted_actions = self.triageAgent.predict(self.world.state,"TriageAg1",legalActions,horizon=0)#not sure if this is the correct function

        # step the sim
        self.world.step(debug=result0)

        # Get some info after the step
        legalActions_after = self.triageAgent.getActions()
        agent_state_after = self.triageAgent.getState('loc')
        reward_after = self.triageAgent.reward()
        other_after = self.triageAgent.getAttribute('R',model='TriageAg10')

        return result0


if __name__ == "__main__":
    sim = GuiTestSimClean()
    for step in range(10):
        print(step)
        result = sim.run_sim()
