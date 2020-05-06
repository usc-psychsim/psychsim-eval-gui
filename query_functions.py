"""
Query function definitions used by psychsim gui
"""


class PsychSimQuery:
    def __init__(self):
        pass

    def query_all(self, planning_agent, action, cycle, planning_horizon):
        """
        A general query that given a planning agent, one of its action, a cycle number and a certain planning horizon
        it prints out projected actions of different agents and projected resulting states for all agents.
        :param planning_agent:
        :param action:
        :param cycle:
        :param planning_horizon:
        :return:
        """
        pass

    def query_action(self, planning_agent, action, cycle, planning_horizon):
        """
         action specific query, which I can use to look at overall reasoning of a planning agent.
        :param planning_agent:
        :param action:
        :param cycle:
        :param planning_horizon:
        :return:
        """
        pass

    def query_state(self, planning_agent, action, cycle, planning_horizon, state):
        """
        A state specific query which gives access to a certain state. Using this one I can plot some of values during
        reasoning in one cycle and get insight from it
        :param planning_agent:
        :param action:
        :param cycle:
        :param planning_horizon:
        :param state:
        :return:
        """
        pass

    def diff_checker(self, query1, query2):
        """
        Ideally having a diff checker that gets two queries would help, however having the other queries there exist
        a lot of diff checker tools that can be used to see the difference between two queries.
        :param query1:
        :param query2:
        :return:
        """
        pass