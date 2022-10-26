#!/usr/bin/env python3

import math
import rclpy
import random
import numpy as np
from scipy.optimize import minimize, rosen, rosen_der, LinearConstraint
from rclpy.node import Node
from kconn_sim.barrier_certificates import SafetyCertificate, ConnectionCertificate
from kconn_sim.agent import Agent
from kconn_sim.cluster import Cluster
from kconn_sim.network import K0Network, Network
from kconn_sim.plotting import *
from time import sleep
from sklearn.cluster import KMeans
from scipy.spatial.distance import cdist

class Simulation(Node):

    def __init__(self):

        super().__init__('MultiAgentSim')

        self.num_agents =  20
        self.type0 = 15
        self.type1 = 5

        self.r_conn = 25
        self.r_safety = 1

        assert self.num_agents == (self.type0 + self.type1)

        self.k0 = 2
        self.k1 = 3

        self.n_clust = self.type1

        self.control_magnitude = 1 #move at 1 m/s
        
        self.env = {0:np.array((-100,100,0)),
                         1: np.array((100,100,0)),
                         2: np.array((-100,-100,0))}

        self.locations = np.array((1,1,1)) 
        self.swarm_control = None
        
        self.swarm = list()
        self.clusters = list()

        self.__init_swarm__()
        self.cycle()
        
        
    def __init_swarm__(self):
        # add layer1 agents to swarm
        for i in range(self.type0):
            
            self.swarm.append( Agent(i,
                                     np.append(np.random.randint(-5,5,size=2), np.array((0))),
                                     self.env[random.randint(0,2)],
                                     0) )
        # add layer 2 agents to swarm 
        for i in range(self.type1):
            self.swarm.append( Agent(i+self.type0,
                                     np.append(np.random.randint(-5,5,size=2),np.array((1))),
                                     self.env[random.randint(0,2)],
                                     1) )
        # initialize the clusters 
        for i in range(self.n_clust):
            self.clusters.append( Cluster(i) ) 
            
        self.get_logger().info('Swarm Initialized')


    def locs_to_numpy(self):
        locs = list()
        for ag in self.swarm:
            locs.append(ag.location)

        self.locations =  np.array(locs)
        
    def cluster(self):

        locs = list()

        for ag in self.swarm:
            locs.append(ag.location)
        X = np.array( locs[0:self.type0] )

        km = KMeans(n_clusters = self.n_clust, random_state = 0).fit(X)

        return km.labels_, km.cluster_centers_

    def matching(self, centroids):
        # TODO: make this resistant if type0/type1 is not int -- DONE

        W = cdist(self.locations[self.type0:],centroids, 'euclidean')
        print(W)
        for iter, ag in enumerate(self.swarm[self.type0:]):
            ag.cluster = np.argmin(W[iter])
            W[:,ag.cluster] = np.inf
        
        for cluster in self.clusters:
            cluster.add_members( self.swarm[self.type0:] )

    def calc_control_vector(self):
        control_vector = np.zeros((1,3))
        for ag in self.swarm:
            theta = math.atan2(ag.location[1],ag.location[0]) - math.atan2(self.env[ag.task][1], self.env[ag.task][0])
            control_vector[0] = self.magnitude * math.cos(theta)
            control_vector[1] = self.magnitude * math.sin(theta)

            ag.set_desired_control(control_vector)

    def set_swarm_control(self):
        for ag in self.swarm:
            u = ag.desired_control
            if ag._id == 0:
                self.swarm_control = u
            else:
                self.swarm_control = np.concatenate((self.swarm_control,u), axis=None)
                
    def get_constraints(self):
        pass

    def optimize(self):
        func = lambda u : np.sum( np.linalg.norm(u - self.swarm_control)**2 )
        cons = ({'type': 'ineq', 'fun': lambda 
            
    def cycle(self):

        Bs = SafetyCertificate(self.r_safety, self.swarm, 1)
        Bc = ConnectionCertificate(self.r_conn, self.swarm, 1)
        
        while rclpy.ok():

            labels, centroids = self.cluster()

            for iter, ag in enumerate( self.swarm[:self.type0] ):
                ag.cluster = labels[iter]

            for cluster in self.clusters:
                cluster.set_members( self.swarm )
                cluster.set_centroid( centroids[cluster.cluster_id] )
            self.locs_to_numpy()

            self.matching(centroids)
            
            k0net = K0Network(self.clusters, self.k0)

            net = Network(self.clusters, self.swarm, k0net, self.k0, self.k1, self.type0, self.type1)
            net.connect()
            
            for ag in self.swarm:
                ag.set_connections(net.connections)
                ag.set_desired_control(float(self.control_magnitude))
                print(ag)
                
            Bs.construct_A()
            Bc.construct_A(net.connections)
            self.set_swarm_control()
            print(self.swarm_control)
            print(self.swarm_control.shape)
            
            print((net.connections))

            break
            #sleep(1)

            
if __name__ == "__main__":
    rclpy.init()

    Simulation()
