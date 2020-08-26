"""Analytic concept based on MaRiQ by Carlsson and Mattson 
http://uu.diva-portal.org/smash/record.jsf?pid=diva2%3A1323684&dswid=-2165

Results – Single Risks
* Estimated risks: All risks listed with ID, name, and calculated mean expected loss
* Top 10 Risks: Sorted list of the ten risks with the highest computed mean expected loss
* Heatmap: Based on the mean likelihood and mean impact of the top 10-prioritized risks
* Uncertainty: Each line represents the 90% interval of simulated impacts. Marke of mean of simulated impact.
Results - Total Risk
* Provides a cumulative frequency plot, in our tool called impact exceedance graph. 
The impact exceedance graph visualizes the combined risk impact. 
* Blue curve represents the simulated outcomes of the total risk impact - the probability of the impact exceeding a specific value. 
* Red curve represents the total risk tolerance, as stated by the user in the Estimations-worksheet.
"""

import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import itertools

class MaRiQ:

    def __init__(self, simulation_result, risk_tolerance):
        self.risk_id = simulation_result["summary"]["risk_list"].risk_id_list()
        self.num_iter = simulation_result["summary"]["number_of_iterations"]
        self.no_risks = len(self.risk_id)
        total_outcome = np.zeros(shape=(self.no_risks, self.num_iter))
        j = 0
        for i in simulation_result["results"]:
            total_outcome[j]=(i["total"])
            j += 1
        self.total_risk_matrix = total_outcome.sum(axis=0)
        self.mariq_data = []
        self._set_stats(simulation_result["results"])
        self.total_risk_tolerance = risk_tolerance
        

    def _set_stats(self, simulation_dict):
        risk_id = []
        impact = []
        mean_frequency = []
        mean_impact = [] 
        mean_expected_loss = []

        for i in simulation_dict:
            risk_id.append(i["id"])
            impact.append(i["single_risk_impact"])
            mean_frequency.append(sum(i["frequency"])/self.num_iter)
            mean_impact.append(sum(i["impact"])/self.num_iter)
            mean_expected_loss.append(sum(np.multiply(i["frequency"], i["single_risk_impact"]))/self.num_iter)
        
        self.mariq_data = {
            "id" : risk_id,
            "impact" : impact,
            "mean_frequency": mean_frequency,
            "mean_impact" : mean_impact,
            "mean_expected_loss" : mean_expected_loss
        }

        
    def single_risk_analysis(self, top_number=10):
        # Uncertainty - box plot of impact
        uncertainty_ids_sorted = self._sort_data('id', 'mean_expected_loss')[::-1]
        uncertainty_data = self._sort_data('impact', 'mean_expected_loss')[::-1]
        uncertainty_fig = go.Figure()
        for i in range(0,top_number,1):
           uncertainty_fig.add_trace(go.Box(y=uncertainty_data[i], name=uncertainty_ids_sorted[i]))
        uncertainty_fig.show()


        # Heatmap - mean likelihood + mean impact
        heatmap_ids = self._sort_data('id', 'mean_expected_loss')[::-1]
        heatmap_frequency = self._sort_data('mean_frequency', 'mean_expected_loss')[::-1]
        heatmap_impact = self._sort_data('mean_impact', 'mean_expected_loss')[::-1]

        heatmap_fig = px.scatter(x=heatmap_frequency[:top_number], y=heatmap_impact[:top_number], text=heatmap_ids[:top_number])
        heatmap_fig.show()
        
        # Top 10 Risks - mean expected loss
        top10_ids = self._sort_data('id', 'mean_expected_loss')[::-1]
        top10_mean_expected_loss = self._sort_data('mean_expected_loss', 'mean_expected_loss')[::-1]
        top10_fig = go.Figure(data=[go.Table(header=dict(values=['Risk ID', 'Risk Level'], align='left'),
                 cells=dict(values=[top10_ids[:10], top10_mean_expected_loss[:10]], align='left'))
                     ])
        top10_fig.show()

        # Estimated risks -  mean expected loss
        risk_list_ids = self._sort_data('id', 'id')
        risk_list_mean_expected_loss = self._sort_data('mean_expected_loss', 'id')
        risk_list_fig = go.Figure(data=[go.Table(header=dict(values=['Risk ID', 'Risk Level'], align='left'),
                 cells=dict(values=[risk_list_ids, risk_list_mean_expected_loss], align='left'))
                     ])
        risk_list_fig.show()

    
    def _sort_data(self, key, sortby):
        return np.array([self.mariq_data[key][x] for x in np.argsort(self.mariq_data[sortby])])



    def total_risk_analysis(self):
        sorted_array = np.sort(self.total_risk_matrix)
        max_outcome = np.percentile(sorted_array, 99)
        risk_buckets = np.arange(0, max_outcome+1, max_outcome/200)
        counter = np.zeros(shape=(len(risk_buckets),1))
        i = 0
        k = 0
        for i in range(0,len(risk_buckets)):
            for x in sorted_array:
                if risk_buckets[i] < x : 
                    k += 1
            counter[i] = k
            k = 0
        y1 = (counter/self.num_iter)
        total_risk = list(itertools.chain.from_iterable(y1))

        trt = []
        for i in self.total_risk_tolerance[1]:
            trt.append(i/100)
        fig = go.Figure()
        fig.layout = go.Layout(yaxis=dict(tickformat=".2%"))
        fig.add_trace(go.Scatter(x=risk_buckets, y=total_risk,
                            mode='lines',
                            line_color='red',
                            name='Total Risk'))
        fig.add_trace(go.Scatter(x=self.total_risk_tolerance[0], y=trt,
                            mode='lines+markers',
                            line_color='blue',
                            name='Tolerance'))                   
        fig.show()

