"""
...
"""
import logging

from atomic.bin import model_inference as mi
from atomic.parsing.replayer import replay_parser, parse_replay_args

DATAFILE = "C:\\Users\Chris Turner\Documents\GitHub\\asist_data\study-2_2021.06_HSRData_TrialMessages_Trial-T000474_Team-TM000137_Member-na_CondBtwn-1_CondWin-SaturnA_Vers-4.metadata"
CONFIGFILE = "C:/Users/Chris Turner/Documents/GitHub/atomic/config/phase2.ini"

class ModelInference:
    def __init__(self):
        """
        The following script is modified from the __main__ of atomic/bin/model_inference.py.
        Instead of passing command line arguments, arguments are passed through the 'arg_list' variable
        Due to how model_inference.py is written, the entire data is passed and stepped through and stored during init.
        The run_step method allows the PsychSimGui to step through this pre-stored data.
        """

        parser = replay_parser()
        parser.add_argument('--reward_file', help='Name of CSV file containing alternate reward functions')
        parser.add_argument('-c','--clusters', help='Name of CSV file containing reward clusters to use as basis for player models')
        arg_list = [DATAFILE,
                    "--config",
                    CONFIGFILE]
        self.args = parse_replay_args(parser, arg_list=arg_list)
        if self.args['clusters']:
            import atomic.model_learning.linear.post_process.clustering as clustering

            reward_weights, cluster_map, condition_map = mi.load_clusters(self.args['clusters'])
            mi.AnalysisParseProcessor.condition_dist = condition_map
            mi.apply_cluster_rewards(reward_weights)
        elif self.args['reward_file']:
            import atomic.model_learning.linear.post_process.clustering as clustering

            mi.apply_cluster_rewards(clustering.load_cluster_reward_weights(self.args['reward_file']))
        self.replayer = mi.Analyzer(self.args['fname'], rddl_file=self.args['rddl'], action_file=self.args['actions'], feature_output=self.args['feature_file'], aux_file=self.args['aux'], logger=logging)

        self.replayer.parameterized_replay(self.args)

        self.sim_steps = len(self.replayer.debug_data)
        self.current_step = 0

    def run_step(self):
        """
        Extract the step result for the GUI at the current step.
        """
        result = self.replayer.debug_data[self.current_step]
        self.current_step += 1
        return result


if __name__ == "__main__":
    sim = ModelInference()
    sim.run_step()
