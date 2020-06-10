import sys
print(sys.path)
sys.path.insert(1, "../../atomic")
sys.path.insert(1, "../../atomic_domain_definitions")

from psychsim.world import World, WORLD
from psychsim.pwl import stateKey, actionKey
from new_locations_fewacts import Locations, Directions
from victims_fewacts import Victims
from SandRMap import getSandRMap, getSandRVictims, getSmallSandRMap, getSmallSandRVictims, checkSRMap
from helpers import testMMBelUpdate, setBeliefs, setBeliefsNoVics
from ftime import FatherTime


class GuiTestSim2():
    def __init__(self):
        self.sim_steps = 10
        self.horizon = 4

        # MDP or POMDP
        Victims.FULL_OBS = True

        ##################
        ##### Get Map Data
        SandRLocs = getSmallSandRMap()
        SandRVics = getSmallSandRVictims()
        ##################

        self.world = World()
        # k = self.world.defineState(WORLD, 'seconds', int)
        # self.world.setFeature(k, 0)

        self.triageAgent = self.world.addAgent('TriageAg1')
        self.agent = self.world.addAgent('ATOMIC')
        clock = FatherTime(self.world, False)

        VICTIMS_LOCS = list(SandRVics.keys())
        VICTIM_TYPES = [SandRVics[v] for v in VICTIMS_LOCS]
        Victims.world = self.world
        Victims.makeVictims(VICTIMS_LOCS, VICTIM_TYPES, [self.triageAgent.name], list(SandRLocs.keys()))
        Victims.makePreTriageActions(self.triageAgent)
        Victims.makeTriageAction(self.triageAgent)

        Victims.P_VIC_FOV = (1.0 - Victims.P_EMPTY_FOV) / len(Victims.victimAgents)

        ################# Locations and Move actions
        Locations.EXPLORE_BONUS = 0
        Locations.world = self.world
        Locations.makeMapDict(SandRLocs)
        Locations.makePlayerLocation(self.triageAgent, "BH2")

        ## These must come before setting triager's beliefs
        self.world.setOrder([{self.triageAgent.name}])

        ## Set players horizons
        self.triageAgent.setAttribute('horizon', self.horizon)
        # triageAgent.setAttribute('selection', 'random')

    def run_step(self):
        self.result0 = {'TriageAg1': {}}
        self.result1 = {'ATOMIC': {'TriageAg1': {}}}

        self.world.step(debug=self.result0)
        return_result = {"WORLD_STATE": self.world.state,
                         "AGENT_STATE": self.result0}
        return return_result

if __name__ == "__main__":
    sim = GuiTestSim2()
    for step in range(sim.sim_steps):
        res = sim.run_sim()
    pass
