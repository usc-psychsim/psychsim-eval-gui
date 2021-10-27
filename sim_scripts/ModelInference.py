"""
...
"""
import logging
import configparser

from atomic.bin import model_inference as mi
from atomic.parsing.replayer import replay_parser, parse_replay_args


class ModelInference:
    def __init__(self):
        """
        The following script is modified from the __main__ of atomic/bin/model_inference.py.
        Instead of passing command line arguments, arguments are passed through the 'arg_list' variable
        Due to how model_inference.py is written, the entire data is passed and stepped through and stored during init.
        The run_step method allows the PsychSimGui to step through this pre-stored data.
        """
        datafile, configfile = self.get_paths()

        parser = mi.model_cmd_parser()
        arg_list = [datafile,
                    "--config",
                    configfile]
        self.args = parse_replay_args(parser, arg_list=arg_list)

        self.replayer = mi.Analyzer(self.args['fname'], self.args['trials'], self.args['config'], rddl_file=self.args['rddl'], action_file=self.args['actions'], aux_file=self.args['aux'], logger=logging, output=self.args['output'])

        self.replayer.parameterized_replay(self.args, simulate=False)

        self.sim_steps = len(self.replayer.debug_data)
        if self.args['number'] > 0:
            self.sim_steps = self.args['number']
        self.current_step = 0

    def get_paths(self):
        """
        This gets the datafile and model_inference.py config file from the GUI config
        """

        config = configparser.ConfigParser()
        config.read('config.ini')
        datafile = config['ASIST_PATHS']['datafile']
        configfile = config['ASIST_PATHS']['configfile']
        return datafile, configfile

    def run_step(self):
        """
        Extract the step result for the GUI at the current step.
        """
        result = self.replayer.decisions[self.args['fname'][0]]
        print(result)
        self.current_step += 1
        return result


if __name__ == "__main__":
    sim = ModelInference()
    sim.run_step()
