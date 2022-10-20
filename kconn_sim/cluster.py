import numpy as np


class Cluster:

    def __init__(self, iden):

        self.cluster_id = iden
        self.members = list()
        self.centroid = None

        self.index_type0 = list()
        self.index_type1 = list()

        self.iter = 0
        
    def __str__(self):
        return "Members: %s\nCentroid: %s" %(self.members, self.centroid)

    def __len__(self):
        """ return the number of nodes in the cluster """
        return len(self.members)
    
    def set_members(self, swarm):
        self.members.clear()
        self.iter = 0
        
        for ag in swarm:
            if ag.cluster == self.cluster_id:
                self.members.append( ag._id )
                self.index_type0.append(self.iter)

    def add_members(self, swarm):
        for ag in swarm:
            if ag.cluster == self.cluster_id:
                self.members.append( ag._id )
                self.index_type1.append(self.iter)
                
    def set_centroid(self, center):
        self.centroid = center














