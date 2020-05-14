# import sys
# print(sys.path)
# sys.path.insert(1, "/home/chris/Documents/GLASGOW_MARSELLA/atomic")
# sys.path.insert(1, "/home/chris/Documents/GLASGOW_MARSELLA/atomic_domain_definitions")

from psychsim.world import World, WORLD
from psychsim.pwl import stateKey, actionKey
# from new_locations_fewacts import Locations, Directions
from victims_fewacts import Victims
from new_locations import Locations, Directions
# from victims import Victims
from SandRMap import getSandRMap, getSandRVictims, getSmallSandRMap, getSmallSandRVictims, checkSRMap
from helpers import testMMBelUpdate, setBeliefs

from psychsim.pwl import stateKey, Distribution, actionKey, VectorDistributionSet, ActionSet

from SimBase import SimBase

class GuiTestSim2(SimBase):
    def __init__(self):
        self.sim_steps = 45
        self.horizon = 4

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

        triageAgent = self.world.addAgent('TriageAg1')
        agent = self.world.addAgent('ATOMIC')

        VICTIMS_LOCS = list(SandRVics.keys())
        VICTIM_TYPES = [SandRVics[v] for v in VICTIMS_LOCS]
        Victims.world = self.world
        Victims.makeVictims(VICTIMS_LOCS, VICTIM_TYPES, [triageAgent.name], list(SandRLocs.keys()))
        Victims.makePreTriageActions(triageAgent)
        Victims.makeTriageAction(triageAgent)

        ################# Locations and Move actions
        Locations.EXPLORE_BONUS = 0
        Locations.world = self.world
        Locations.makeMapDict(SandRLocs)
        Locations.makePlayerLocation(triageAgent, "BH2")

        ## These must come before setting triager's beliefs
        self.world.setOrder([{triageAgent.name}])

        ## Set players horizons
        triageAgent.setAttribute('horizon', self.horizon)
        # triageAgent.setAttribute('selection', 'random')

    def run_sim(self):
        self.result0 = {'TriageAg1': {}}
        self.result1 = {'ATOMIC': {'TriageAg1': {}}}

        self.world.step(debug=self.result0)
        return self.result0

if __name__ == "__main__":
    sim = GuiTestSim2()
    sim.run_sim()