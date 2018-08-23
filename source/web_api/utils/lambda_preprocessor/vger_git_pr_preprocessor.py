from __future__ import print_function
from __future__ import division
import datetime
from vger_redshift_preprocessor import VgerRedshiftPreprocessor


class VgerGitPRPreprocessor(VgerRedshiftPreprocessor):
    def __init__(self, event):
        VgerRedshiftPreprocessor.__init__(self, event)

    # Get closed pull requests and the total week list for further calculation
    def get_merged_pull_requests(self):
        pr_counts = self.redshift.getMergedPrCount(
            self.param["project_id"], self.param["repo_list"],
            self.param["date_since"], self.param["date_until"]
        )
        num_weeks = (self.param["date_until"] - self.param["date_since"]).days // 7
        total_weeks_list = [self.param["date_since"] + datetime.timedelta(weeks=i) for i in range(num_weeks + 1)]

        # Iterate through the generated weeks
        # TODO number with trailing 'L' is no longer available in python 3.6
        for index, week in enumerate(total_weeks_list):
            # Compare with db data, and fill up any missing weeks
            if index < len(pr_counts):
                if week != pr_counts[index][1]:
                    pr_counts.insert(index, (0L, week))
            else:
                pr_counts.insert(index, (0L, week))

        return pr_counts, total_weeks_list

    # Get average lead time for pull requests and the total week list for further calculation
    def get_merged_pull_requests_timestamp(self):
        pr_lead_times = self.redshift.get_merged_pull_requests_timestamp(
            self.param["project_id"], self.param["repo_list"],
            self.param["date_since"], self.param["date_until"]
        )
        num_weeks = (self.param["date_until"] - self.param["date_since"]).days // 7
        total_weeks_list = [self.param["date_since"] + datetime.timedelta(weeks=i) for i in range(num_weeks + 1)]
        return pr_lead_times, total_weeks_list

    def get_failed_pull_requests_volume(self):
        failed_pr_volumes = self.redshift.get_failed_pull_requests_volume(
            self.param["project_id"], self.param["repo_list"],
            self.param["date_since"], self.param["date_until"]
        )
        num_weeks = (self.param["date_until"] - self.param["date_since"]).days // 7
        total_weeks_list = [self.param["date_since"] + datetime.timedelta(weeks=i) for i in range(num_weeks + 1)]

        return failed_pr_volumes, total_weeks_list
