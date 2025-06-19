gamelogs = "{replay_html here}"


TRACKER_DICT = {
    "counter_hand_": "Hand Counter",
    "tracker_m_": "MC",
    "tracker_pm_": "MC Production",
    "tracker_s_": "Steel",
    "tracker_ps_": "Steel Production",
    "tracker_u_": "Titanium",
    "tracker_pu_": "Titanium Production",
    "tracker_p_": "Plant",
    "tracker_pp_": "Plant Production",
    "tracker_pe_": "Energy Production",
    "tracker_e_": "Energy",
    "tracker_h": "Heat",
    "tracker_ph_": "Heat Production",
    "tracker_tagBuilding_": "Count of Building tags",
    "tracker_tagSpace": "Count of Space tags",
    "tracker_tagScience_": "Count of Science tags",
    "tracker_tagEnergy_": "Count of Power tags",
    "tracker_tagEarth_": "Count of Earth tags",
    "tracker_tagJovian_": "Count of Jovian tags",
    "tracker_tagCity_": "Count of City tags",
    "tracker_tagPlant_": "Count of Plant tags",
    "tracker_tagMicrobe_": "Count of Microbe tags",
    "tracker_tagAnimal_": "Count of Animal tags",
    "tracker_tagWild_": "Count of Wild tags",
    "tracker_tagEvent_": "Count of played Events cards",
    "tracker_ers_": "Steel Exchange Rate",
    "tracker_eru_": "Titanium Exchange Rate"
}


player_ids = [86949293, 96014413] # Example IDs
player_counts_per_move = []

tracker_values = set(TRACKER_DICT.values())

player_data = {
    player_id: {value: 0 for value in tracker_values}
    for player_id in player_ids
}


num_moves = max([int(move["move_id"]) for move in gamelogs["data"]["data"] if move["move_id"] != None])

for i in range(1, num_moves+1):
    move = [move for move in gamelogs["data"]["data"] if move["move_id"] == f"{i}"][0]
    
    for submove in move["data"]:        
        
        for tracker_key in TRACKER_DICT:
        
            if "counter_name" in submove["args"] and submove["args"]["counter_name"].startswith(tracker_key):
                
                counter_value = submove["args"]["counter_value"]
                player_id = int(submove["args"]["player_id"])
                tracker_name = TRACKER_DICT[tracker_key]
                
                print("Move", i, ":", player_id, counter_value)
                
                player_data[player_id][tracker_name] = counter_value
            
    player_counts_per_move.append({
        "move_index": i,
        "data": player_data
    })