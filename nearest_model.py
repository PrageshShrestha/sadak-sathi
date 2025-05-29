
class shortest_distance:
    def __init__(self,  G = G_saved):
        """
        Initialize the OSM graph handler with two coordinates.
        Fetches the road network graph around the given points.
        """

        #print(self.distance)
        # Load OSM graph around the midpoint of the two coordinates
       # midpoint = ((lat1 + lat2) / 2, (lon1 + lon2) / 2)
        #print(midpoint)
        self.G = G
        # self.G = ox.graph_from_point(midpoint, dist=self.distance*.65, network_type="drive")
        # x , _ = ox.plot_graph(self.G)
        # G_saved = ox.save_graphml(self.G , "Nepal_pregraph.graphml")
        # print(G_saved)
        edges_to_remove = []
        for u, v, data in self.G.edges(data=True):
            if 'highway' in data:
                if data['highway'] in ['footway', 'path', 'pedestrian', 'steps']:
                    edges_to_remove.append((u, v))

        self.G.remove_edges_from(edges_to_remove)
        print("made graph")
        self.traversed = []
        self.discarded = []
        self.total = 0
    def haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate the Haversine distance between two geographic coordinates.
        Returns distance in meters.
        """
        R = 6367444.5  # Radius of the Earth in meters
        phi1, phi2 = np.radians(lat1), np.radians(lat2)
        delta_phi = np.radians(lat2 - lat1)
        delta_lambda = np.radians(lon2 - lon1)

        a = np.sin(delta_phi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2.0) ** 2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

        return R * c



    def get_connected_nodes(self, node_id):
        """Gets the nodes connected to the given node."""
        return list(self.G.neighbors(node_id))



    def get_nearest_edge_nodes(self, lat, lon):
        """Finds the two nodes forming the edge closest to a given coordinate."""
        nearest_edge = ox.distance.nearest_edges(self.G, X=lon, Y=lat)

        if len(nearest_edge)==3:
            return nearest_edge[:2]  # Returns (node1, node2)
        else:
            return nearest_edge[0]
    def get_node_data(self, node_id):
        """Retrieves node details such as latitude and longitude."""
        if node_id in self.G.nodes:
            some_var = self.G.nodes[node_id]
            return some_var["y"] , some_var["x"]
        return None
    def valid_node_source(self , nodes):
        if len(nodes)==1:
            lat, lon = self.get_node_data(nodes)
            return nodes , lat , lon
        else:
            list_hav = []
            for node in nodes:
                lat,lon = self.get_node_data(node)
                hav_distance = self.haversine_distance(self.lat1 , self.lon1 , lat , lon)
                list_hav.append((node , hav_distance))
            sorted_list = sorted(list_hav , key = lambda x:x[1] , reverse = False)
            return sorted_list[0]
    def valid_node_target(self , nodes):
        if len(nodes)==1:
            lat,lon = self.get_node_data(nodes)
            return nodes , lat , lon
        else:
            list_hav = []
            for node in nodes:
                lat,lon = self.get_node_data(node)
                hav_distance = self.haversine_distance(self.lat2 , self.lon2 , lat , lon)
                list_hav.append((node , hav_distance))
            sorted_list = sorted(list_hav , key = lambda x:x[1] , reverse = False)
            #print(sorted_list)
            return sorted_list[0]

    def grwd(self, node1, node2):  # get real-world distance

      G = self.G
      distance = nx.shortest_path_length(G, source=node1, target=node2, weight='length')
      return distance

    def actual_output(self):
       # print(self.G)
        first_node = self.get_nearest_edge_nodes(self.lat1 , self.lon1)
        last_node = self.get_nearest_edge_nodes(self.lat2 , self.lon2)
        actual_fn , _  = self.valid_node_source(first_node)
        actual_ln , dist_acl  = self.valid_node_target(last_node)
        print(actual_ln , dist_acl)
        print(" the coordinates of nearest node to target is :")
        print(self.get_node_data(actual_ln))
        ad = 1
        current_node = actual_fn
        self.traversed.append(actual_fn)
        G = self.G
        while ad != 0 :
            #print(self.traversed)


            neighbor_nodes = self.get_connected_nodes(current_node)
            is_subset = set(neighbor_nodes).issubset(set(self.discarded))
            if is_subset:
                print(neighbor_nodes)
                print("subset meet")
                self.discarded.append(current_node)

                try:
                  self.traversed.pop()
                  current_node = self.traversed[-1]
                except:
                  print("first node")
                  current_node = actual_fn
                continue
            neigh_data=[]
            for i in range(len(neighbor_nodes)):

                i = neighbor_nodes[i-1]
                print(i)
                print(self.get_node_data(i))

                if i == actual_ln:
                    print(f" the actual node is:{i}")
                    self.traversed.append(i)

                    ad = 0
                    break
                if i in self.discarded:
                    #print(" A discarded coupon found , " , i)
                    continue
                if G.nodes[i]["street_count"]<2:
                    self.discarded.append(i)
                    #print(f"the deadend node is {i}")
                    continue
                try:
                  dist = self.grwd(i , current_node)
                except:
                  dist = 10000000000000
                #print(f" the distance is {dist}")
                lat_new , lon_new = self.get_node_data(i)
                h_dist = self.haversine_distance(lat_new , lon_new , self.lat2 , self.lon2)
                #print(f"the h_dist is {h_dist}")

                actual_distance = dist+h_dist
                neigh_data.append((actual_distance , i))
                #print(f"the actual distance is {actual_distance}")

            try:
                if ad==0:
                  break

                sorted_nd = sorted(neigh_data ,key = lambda x:x[0] , reverse = False)
                #print("The length of sorted_nd is:",len(sorted_nd))
                #print(sorted_nd)
                for k in sorted_nd:
                  if k[1] not in self.traversed:
                      self.traversed.append(k[1])
                      self.total+=1

                      current_node = k[1]
                      #print(f" new coordinate added {k[1]}")
                      break
                  else:
                      self.discarded.append(k[1])
                      self.traversed.pop()
                      current_node = self.traversed[self.total-1]

                      #print("current_node is:",current_node)
            except Exception as e :

                ad = 1

        return self.traversed

    # def get_route_coordinates(self):
    #   """
    #   Given an OSMnx graph and a list of node IDs, return a list of coordinates
    #   (lat, lon) that represent the full path between those nodes.
    #   """
    #   self.actual_output()
    #   G = self.G
    #   node_list = self.traversed
    #   coordinates = []

    #   for i in range(len(node_list) - 1):
    #       u = node_list[i]
    #       v = node_list[i + 1]

    #       if G.has_edge(u, v):
    #           edge_data = G.get_edge_data(u, v)

    #           # Some edges might have multiple parallel edges (e.g., multiple lanes)
    #           # Choose the first one arbitrarily
    #           if isinstance(edge_data, dict):
    #               edge = edge_data[list(edge_data.keys())[0]]
    #           else:
    #               edge = edge_data

    #           # If geometry is available, use it
    #           if 'geometry' in edge:
    #               xs, ys = edge['geometry'].xy
    #               segment_coords = list(zip(ys, xs))  # Convert to (lat, lon)
    #           else:
    #               # Fallback to straight line between nodes
    #               point_u = (G.nodes[u]['y'], G.nodes[u]['x'])
    #               point_v = (G.nodes[v]['y'], G.nodes[v]['x'])
    #               segment_coords = [point_u, point_v]

    #           # Avoid repeating last coordinate from previous segment
    #           if coordinates and segment_coords[0] == coordinates[-1]:
    #               segment_coords = segment_coords[1:]

    #           coordinates.extend(segment_coords)

    #       else:
    #           print(f"No direct edge between node {u} and node {v}!")

    #   coordinates = str(coordinates).replace('(', '[').replace(')', ']')  # JS-style format
    #   return coordinates

    def get_route_coordinates(self):
        """
        Given an OSMnx graph and a list of node IDs, return a list of coordinates
        (lat, lon) that represent the full path between those nodes in JavaScript dict format.
        """
        self.actual_output()
        G = self.G
        node_list = self.traversed
       # print(node_list)
        coordinates = []

        for i in node_list:
          id = i
          lat , lon = G.nodes[i]["y"] , G.nodes[i]["x"]
          coordinates.append({"id":id , "lat":lat , "lon":lon})
        coordinates = str(coordinates).replace('(', '[').replace(')', ']')  # JS-style format
        return coordinates



    def get_node_coordinates_from_graph(self , lat1, lon1, lat2, lon2 ):
        """
        Given a graph from OSMnx and a list of node IDs, return the coordinates of each node.
        Returns a string formatted as a JavaScript dictionary of node IDs with coordinates.
        """
        self.lat1, self.lon1 = lat1, lon1
        self.lat2, self.lon2 = lat2, lon2
        self.distance = self.haversine_distance(lat1, lon1, lat2, lon2)
        self.actual_output()
        coordinates = {}
        node_ids = self.traversed + self.discarded
        # Loop through each node ID
        graph = self.G
        for node_id in node_ids:
            if node_id in graph.nodes:
                # Get the latitude and longitude for the node
                lat = graph.nodes[node_id]['y']
                lon = graph.nodes[node_id]['x']
                coordinates[node_id] = {"lat": lat, "lon": lon}

        # Convert the dictionary to JavaScript object format
        return str(coordinates).replace("'", '"')  # Replace single quotes with double quotes for JS compatibility



src_lat , src_lon =27.590656, 85.622013


tgt_lat , tgt_lon =27.746617, 85.087761


var1 = shortest_distance()
