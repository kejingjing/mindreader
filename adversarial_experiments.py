from show_models import *


def condition_advers_basicPO_model(runner_model, start, other_start, t, path, future_detections=False):
	Q = ProgramTrace(runner_model)
	Q.condition("run_start", start)
	Q.condition("other_run_start", other_start)
	Q.condition("t", t)

	# condition on previous time steps
	for prev_t in xrange(t):
		#if prev_t == (t-1):
		Q.condition("run_x_"+str(prev_t), path[prev_t][0])
		Q.condition("run_y_"+str(prev_t), path[prev_t][1])
		Q.condition("detected_t_"+str(prev_t), False)
		
	# condition future detections
	for i in xrange(t, 40):
		Q.condition("detected_t_"+str(i), future_detections)

	return Q

def E1(locs, poly_map, isovist, directory="Experiment_1", PS=1, SP=1):
	x1,y1,x2,y2 = poly_map
	sim_id = str(int(time.time()))

	# personal machine
	#newpath = "/Users/Iris/Documents/Repos/mindreader/PO_forward_runs/"+directory+"/"+str(sim_id) 
	# lab machine
	newpath = "/home/iris/Desktop/mindreader/PO_forward_runs/"+directory+"/"+str(sim_id) 
	
	if not os.path.exists(newpath):
	    os.makedirs(newpath)

	chaser_start = 6
	chaser_path = [locs[chaser_start]]

	runner_start = 2
	runner_path = [locs[runner_start]]

	runner_goal = 9

	#---------------------------------------------------------------------------------------------
	#Create model for the Chaser
	chaser_model = BasicRunnerPOM(seg_map=poly_map, locs=locs, isovist=isovist, mode="advers")

	#Create "model" (just the precomputed naive path) for the Runner
	runner_plan = run_rrt_opt( np.atleast_2d(locs[runner_start]), 
		np.atleast_2d(locs[runner_goal]), x1,y1,x2,y2 )
	simulate_time = time_to_reach_goal(runner_plan)
	#---------------------------------------------------------------------------------------------

	# Chaser does not know goal. 
	Q = condition_advers_basicPO_model(chaser_model, chaser_start, runner_start, t+1, chaser_path, future_detections=True)
	post_sample_traces = run_inference(Q, post_samples=PS, samples=SP) 

	inferred_runner_plan = post_sample_traces[0]["other_plan"]


	# for each time step
	for t in xrange(0, simulate_time):

		#[removed planning by inference section here]
		
		# -----------------------------------

		# need to store the locations that they were located so they can condition on them

		plot_movements(chaser_path, runner_path, sim_id, poly_map, locs, t, code="PO-find_eachother", directory="PO_forward_runs/"+directory+"/"+sim_id)
		if runner_detected:
			return True

	return False # for Chaser failed


def planning_by_inference_E1(chaser_model, chaser_start, runner_start, chaser_path, runner_plan, t, poly_map):
	x1, y1, x2, y2 = poly_map
	# RUNNER ----------------------------
	# Runner makes decision for next step
	#runner_next_step = runner_plan[t+1] 
	#------------------------------------
	# CHASER ----------------------------
	# Create a Program Trace and condition it with past detections false, future detections as true, and its own past movements
	Q = condition_advers_basicPO_model(chaser_model, chaser_start, runner_start, t+1, chaser_path, future_detections=True)
	# Run inference for Chaser's next step
	post_sample_traces = run_inference(Q, post_samples=PS, samples=SP) # must decide what to do with my updated beliefs
	# Chaser's Next Step
	inferred_runner_plan = post_sample_traces[0]["other_plan"]
	# --chaser plans to intercept the runner
	# --this is done by planing towards the runner's inferred plan at 6 time steps ahead.
	chasers_new_plan = run_rrt_opt( np.atleast_2d(chaser_path[-1]), 
	np.atleast_2d(inferred_runner_plan[min(t+6, len(inferred_runner_plan)-1)]), x1,y1,x2,y2 )
	chaser_next_step = chasers_new_plan[1] 
	#------------------------------------
	# add to history of true locations for the agents
	runner_path.append(runner_next_step)
	chaser_path.append(chaser_next_step)
	# was runner detected?
	runner_detected = was_other_detected(chaser_next_step, runner_next_step, isovist)

	return chaser_path, runner_path, detected
	


def was_other_detected(agent_loc, other_agent_loc, isovist):
	#Check if they saw one another
	loc = scale_up(agent_loc)
	other_loc = scale_up(other_agent_loc)

	fv = direction(other_loc, loc)
	intersections = isovist.GetIsovistIntersections(loc, fv)
	is_other_seen = isovist.FindIntruderAtPoint(other_loc, intersections)
	return is_other_seen

def time_to_reach_goal(path):
	no_hover_path = []
	for pt in path:
		if abs(pt[0] - path[-2][0]) > .01:
			if abs(pt[1] - path[-2][1]) > 0.01:
				no_hover_path.append(pt)
	no_hover_path.append(path[-2])
	return len(no_hover_path)

#-----------------------------------------------------
# need to implement (but did not since I used previous experiments)
def E2():
	pass

def E3():
	pass

def E4():
	pass
#-----------------------------------------------------






def Experiment_1_Smart_Chaser_vs_Naive_Runner(num=1):
	passing_list = []
	for i in xrange(num):
		passed = E1(locs, poly_map, isovist, directory="Experiment_1", PS=1, SP=16)
		passing_list.append(passed)
	return passing_list

def Experiment_2_Smart_Chaser_vs_Smarter_Runner():
	pass

def Experiment_3_Smartest_Chaser_vs_Smarter_Runner():
	pass

def Experiment_4_Smartest_Chaser_vs_Naive_Runner():
	pass



# for this experiment, I do NOT condition the start and goal locations for the  CHASER ( let's try 0 to 8)

# but I do condition the start and goal for the runner.

# then to show that no matter where the chaser may be going

# the runner will travel through the most stealthy areas. (alleyways... taking the long way.. etc)


# seperates the inference process from printing it on a heatmap
# this lets me run several inferences to collect several paths and later map them
def what_a_stealthy_runner(locs, poly_map, isovist, mode="advers", PS=10, SP=32, inf_type="IS", conditioned=True):
	runner_model = BasicRunnerPOM(seg_map=poly_map, locs=locs, isovist=isovist, mode=mode)
	Q = ProgramTrace(runner_model)

	runner_start = 4
	runner_goal = 8
	Q.condition("run_start", runner_start)
	Q.condition("run_goal", runner_goal)

	# we want to sample from the prior for tha chaser start and goal
	# Q.condition("other_run_start", chaser_start)
	# Q.condition("other_run_goal", chaser_goal)
	t = 0
	Q.condition("t", t)
	
	if conditioned:
		for i in xrange(t):
			Q.condition("detected_t_"+str(i), False)
		for i in xrange(t, 24):
			Q.condition("detected_t_"+str(i), False)
			# if len(smart_runner_path) > i:
			# 	Q.condition("run_x_"+str(i), smart_runner_path[i][0])
			# 	Q.condition("run_y_"+str(i), smart_runner_path[i][1])

	#run_inference_MH
	if inf_type == "IS":
		post_sample_traces = run_inference(Q, post_samples=PS, samples=SP)
	if inf_type == "MH":
		post_sample_traces = run_inference_MH(Q, post_samples=PS, samples=SP)


	paths = []
	other_paths = []
	for trace in post_sample_traces:
		path = trace["my_plan"]
		other_path = trace["other_plan"]

		# remove hovering points on path
		no_hover_path = []
		for pt in path:
			if abs(pt[0] - path[-2][0]) > .01:
				if abs(pt[1] - path[-2][1]) > 0.01:
					no_hover_path.append(pt)
		no_hover_path.append(path[-2])
		paths.append(no_hover_path)

		# remove hovering points on other path
		no_hover_other_path = []
		for pt in other_path:
			if abs(pt[0] - other_path[-2][0]) > .01:
				if abs(pt[1] - other_path[-2][1]) > 0.01:
					no_hover_other_path.append(pt)
		no_hover_other_path.append(other_path[-2])
		other_paths.append(no_hover_other_path)

	return paths, other_paths


# for this experiment I condition the start and goal locations for the chaser to be 3 and 9. 

# then to show that no matter where the runner starts (while conditioning goal to be at 9 as well)

# that the runner will travel through the most stealthy areas. (alleyways... taking the long way.. etc)


# seperates the inference process from printing it on a heatmap
# this lets me run several inferences to collect several paths and later map them
def stealth_runner_given_chaser_locs(locs, poly_map, isovist, mode="advers", PS=10, SP=32, inf_type="IS", runner_start=0):
	runner_model = BasicRunnerPOM(seg_map=poly_map, locs=locs, isovist=isovist, mode=mode)
	Q = ProgramTrace(runner_model)

	runner_goal = 9
	Q.condition("run_start", runner_start)
	Q.condition("run_goal", runner_goal)

	Q.condition("other_run_start", 3)
	Q.condition("other_run_goal", 9)
	t = 0
	Q.condition("t", t)
	
	for i in xrange(t):
		Q.condition("detected_t_"+str(i), False)
	for i in xrange(t, 24):
		Q.condition("detected_t_"+str(i), False)
		# if len(smart_runner_path) > i:
		# 	Q.condition("run_x_"+str(i), smart_runner_path[i][0])
		# 	Q.condition("run_y_"+str(i), smart_runner_path[i][1])

	#run_inference_MH
	if inf_type == "IS":
		post_sample_traces = run_inference(Q, post_samples=PS, samples=SP)
	if inf_type == "MH":
		post_sample_traces = run_inference_MH(Q, post_samples=PS, samples=SP)


	paths = []
	other_paths = []
	for trace in post_sample_traces:
		path = trace["my_plan"]
		other_path = trace["other_plan"]

		# remove hovering points on path
		no_hover_path = []
		for pt in path:
			if abs(pt[0] - path[-2][0]) > .01:
				if abs(pt[1] - path[-2][1]) > 0.01:
					no_hover_path.append(pt)
		no_hover_path.append(path[-2])
		paths.append(no_hover_path)

		# remove hovering points on other path
		no_hover_other_path = []
		for pt in other_path:
			if abs(pt[0] - other_path[-2][0]) > .01:
				if abs(pt[1] - other_path[-2][1]) > 0.01:
					no_hover_other_path.append(pt)
		no_hover_other_path.append(other_path[-2])
		other_paths.append(no_hover_other_path)

	return paths, other_paths




def combine_all_into_heatmap(paths, other_paths, poly_map=None, locs=None, inf_type="IS", PS=10, SP=32, folder="unknown_inference/"):
	#print "runner path: ", no_hover_path
	results = []
	results.append( path_to_heatmap(paths) )
	tmarg = []
	for r in results:
		tmarg.append( np.mean( r, axis=2 ) )
	fig, ax = setup_plot(poly_map, locs, scale = 500)
	plt.xticks([])
	plt.yticks([])
	
	#ax.invert_yaxis()
	cax = ax.imshow( tmarg[0], interpolation='nearest', cmap="jet", origin='lower'); 
	ax.set_title('Runner')
	cbar = fig.colorbar(cax, ticks=[-1, 0, 1])
	cbar.ax.set_yticklabels(['0', '', ''])

	test_id = int(time.time())
	plot_name="PO_forward_runs/"+folder+inf_type+"_advers-starts"+str(test_id)+"-"+str(PS)+"-Runner-"+str(SP)+".eps"
	print "Plot name: ", plot_name
	plt.savefig(plot_name, bbox_inches='tight')

	results = []
	results.append( path_to_heatmap(other_paths) )
	tmarg = []
	for r in results:
		tmarg.append( np.mean( r, axis=2 ) )
	fig, ax = setup_plot(poly_map, locs, scale = 500)
	plt.xticks([])
	plt.yticks([])
	
	#ax.invert_yaxis()
	cax = ax.imshow( tmarg[0], interpolation='nearest', cmap="jet", origin='lower');
	ax.set_title('Chaser')
	cbar = fig.colorbar(cax, ticks=[-1, 0, 1])
	cbar.ax.set_yticklabels(['0', '', ''])

	plot_name="PO_forward_runs/"+folder+inf_type+"_advers_starts-"+str(test_id)+"-"+str(PS)+"-Chaser-"+str(SP)+".eps"
	print "Plot name: ", plot_name
	plt.savefig(plot_name, bbox_inches='tight')


def plot_agent(locs, poly_map, isovist, mode="chaser"):
	rx1,ry1,rx2,ry2 = poly_map
	start = 7
	goal = 4

	path = run_rrt_opt( np.atleast_2d(locs[start]), 
		np.atleast_2d(locs[goal]), rx1,ry1,rx2,ry2 )

	# start-8 to goal-1
	#path = [[0.67500000000000004, 0.92500000000000004], [0.63255478357908257, 0.91627180541238606], [0.59010956715816509, 0.90754361082477197], [0.54766435073724762, 0.89881541623715788], [0.50521913431633014, 0.8900872216495439], [0.46277391789541267, 0.88135902706192981], [0.42032870147449519, 0.87263083247431572], [0.37788348505357766, 0.86390263788670174], [0.35653358792479589, 0.84149378114552198], [0.3623763358999873, 0.79915614021174641], [0.35360451421721967, 0.75671991839425301], [0.34483269253445198, 0.71428369657675961], [0.31423190245059396, 0.69211847706367291], [0.30676543046176979, 0.65074823379423619], [0.30115281775188701, 0.60777991574073731], [0.29554020504200418, 0.56481159768723843], [0.2826052044129625, 0.52576088762546513], [0.25532121104267552, 0.49533838998810387], [0.2625090017684939, 0.45260534139267106], [0.26969679249431228, 0.40987229279723836], [0.28180182663967396, 0.3695556255456921], [0.31352705570149092, 0.34159156805386648], [0.35549599961092604, 0.33080335574113984], [0.39746494352036116, 0.32001514342841314], [0.43874245813891877, 0.30862195166035145], [0.44386260812232065, 0.26559217311194105], [0.4725975902496975, 0.23474906068784063], [0.50470273681078559, 0.2056451547288663], [0.5368078833718738, 0.1765412487698918], [0.56891302993296189, 0.14743734281091744], [0.60179406883805042, 0.11927116309097109], [0.62550640735779983, 0.10136966378933744], [0.5908398890905453, 0.12736986165404424], [ 0.566,  0.146]]
	# start-7 to goal-4
	path = [[0.81499999999999995, 0.59799999999999998], [0.7759947201243943, 0.57912234337627033], [0.73698944024878843, 0.56024468675254069], [0.69798416037318267, 0.54136703012881116], [0.65897888049757691, 0.52248937350508151], [0.61997360062197127, 0.50361171688135187], [0.59071520410802103, 0.48188403611330455], [0.6061149294313255, 0.44543870211582487], [0.57885009103852847, 0.41175775252718594], [0.55158525264573144, 0.37807680293854706], [0.52432041425293441, 0.34439585334990808], [0.49705557586013738, 0.31071490376126909], [0.4564564683561052, 0.30613638740796911], [0.41351854387761661, 0.31101674082050351], [0.37088546506540765, 0.31877550159589541], [0.32825238625319875, 0.3265342623712873], [0.28687135567974092, 0.32843263989852811], [0.25373336272702496, 0.31374826590196814], [ 0.241,  0.34 ]]

	# no_hover_path = []
	# for pt in path:
	# 	if abs(pt[0] - path[-2][0]) > .01:
	# 		if abs(pt[1] - path[-2][1]) > 0.01:
	# 			no_hover_path.append(pt)
	# no_hover_path.append(path[-2])

	# results = []
	# results.append( path_to_heatmap([no_hover_path], ss=5  ))
	# tmarg = []
	# for r in results:
	# 	tmarg.append( np.mean( r, axis=2 ) )
	fig, ax = setup_plot(poly_map, locs, scale = 500)

	#t = len(path)-1
	t = 11

	print path[:t]
	for i in range(0, t):
		ax.plot( [path[i][0]*500, path[i+1][0]*500 ], [ path[i][1]*500, path[i+1][1]*500], 
			color = 'grey', linestyle="-", linewidth=1)
		ax.scatter( path[i][0]*500,  path[i][1]*500, s = 10, facecolors='none', edgecolors='grey')
	ax.scatter( path[t][0]*500,  path[t][1]*500, s = 10, facecolors='none', edgecolors='grey')
		
	plt.xticks([])
	plt.yticks([])
	# #ax.invert_yaxis()
	# cax = ax.imshow( tmarg[0], interpolation='nearest', cmap="jet", origin='lower')#; plt.show()


	#ax.set_title('Smart Runner')
	#cbar = fig.colorbar(cax, ticks=[-1, 0, 1])
	#cbar.ax.set_yticklabels(['0', '', ''])
	plot_name="PO_forward_runs/chaser_test_1.eps"
	plt.savefig(plot_name, bbox_inches='tight')

	#print path


if __name__ == '__main__':
	#plot("test.eps")
	
	locs = None
	poly_map = None
	isovist = None

	map_info = 2

	# ------------- setup for map 2 ---------------
	if map_info == 1:
		locs_map_1 = [[0.4, 0.062] ,
				[0.964, 0.064] ,
				[0.442, 0.37] ,
				[0.1, 0.95] ,
				[0.946, 0.90] ,
				[0.066, 0.538]]
		locs = locs_map_1
		poly_map  = polygons_to_segments( load_polygons( "./map_2.txt" ) )
		isovist = i.Isovist( load_isovist_map( fn="./map_2.txt" ) )

	# ------------- setup for map "paths" large bremen map ---------------
	if map_info == 2:
		locs = [[ 0.100, 1-0.900 ],[ 0.566, 1-0.854 ],[ 0.761, 1-0.665 ],
			[ 0.523, 1-0.604 ],[ 0.241, 1-0.660 ],[ 0.425, 1-0.591 ],
			[ 0.303, 1-0.429 ],[ 0.815, 1-0.402 ],[ 0.675, 1-0.075 ],
			[ 0.432, 1-0.098 ] ]
		poly_map = polygons_to_segments( load_polygons( "./paths.txt" ) )
		isovist = i.Isovist( load_isovist_map() )

	#plots the map and the locations if said so in the function
	#plot(poly_map, plot_name="testing_advers.eps", locs=locs)


	###################################################################################
	#	Adversarial Model - Testing
	###################################################################################

	#runner_model = BasicRunnerPOM(seg_map=poly_map, locs=locs, isovist=isovist, mode="advers")
	#run_unconditioned_basic_partial_model(locs, poly_map, isovist, mode="advers")
	#run_advers_conditioned_basic_partial_model(locs, poly_map, isovist, mode="advers")
	#plot_smart_runner_advers(locs, poly_map, isovist, mode="advers")
	
	###################################################################################
	#	Adversarial Inference - Testing
	###################################################################################

	# for i in xrange(1):
	# 	run_inference_advers_nested_PO(locs, poly_map, isovist, mode="advers", PS=100, SP=64, inf_type="IS")
		#run_inference_advers_PO(locs, poly_map, isovist, mode="advers", PS=100, SP=124, inf_type="MH")
	# for i in xrange(1):
	# 	run_inference_advers_nested_PO(locs, poly_map, isovist, mode="advers", PS=100, SP=16, inf_type="IS")
	# for i in xrange(1):
	# 	run_inference_advers_PO(locs, poly_map, isovist, mode="advers", PS=100, SP=32, inf_type="IS")
	# for i in xrange(1):
	# 	run_inference_advers_PO(locs, poly_map, isovist, mode="advers", PS=100, SP=64, inf_type="IS")
	

	###################################################################################
	#	Adversarial Experiments
	###################################################################################
	
	# result_list = Experiment_1_Smart_Chaser_vs_Naive_Runner(num=1)
	# print result_list

	#plot_agent(locs, poly_map, isovist, mode="chaser")
	#run_inference_advers_PO_chaser_cond(locs, poly_map, isovist, mode="advers", PS=100, SP=128, inf_type="IS")

	#------------------------------------------
	# to run the experiment where we want to see if the runner goes through alley ways if we condition
	# the runner start and goal (on the middlemost model), and the chaser's start and goal
	# we run several experiments where we condition the starting location for the runner at different
	# locations

	# runner_start_list = [0,1,2,4,5,6,7,8]
	# paths = []
	# other_paths = []
	# for runner_start in runner_start_list:
	# 	print "running inference for runner's start: ", runner_start
	# 	_paths, _other_paths = stealth_runner_given_chaser_locs(locs, poly_map, isovist, mode="advers", PS=50, SP=128, inf_type="IS", runner_start=runner_start)
	# 	# paths +=  _paths
	# 	# other_paths += _other_paths


	# 	combine_all_into_heatmap(_paths, _other_paths, PS=50, SP=128)

	# -----------------------------------------

	# to run the experiment where we want to see if the runner goes through alley ways if we condition
	# the runner start and goal (on the middlemost model), and sample from the prior for the 
	# chaser's start and goal locations

	paths = []
	other_paths = []

	cond = True
	P = 50
	S = 128

	_paths, _other_paths = what_a_stealthy_runner(locs, poly_map, isovist, mode="advers", PS=P, SP=S, inf_type="IS", conditioned=cond)
	
	paths +=  _paths
	other_paths += _other_paths
	if cond:
		combine_all_into_heatmap(_paths, _other_paths, poly_map=poly_map, locs=locs, PS=P, SP=S, folder="stealth-cond/")
	else:
		combine_all_into_heatmap(_paths, _other_paths, poly_map=poly_map, locs=locs, PS=P, SP=S, folder="stealth-uncond/")
	# ---------------------------------------