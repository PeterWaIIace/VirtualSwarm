
import threading
import time
import sys

class SwarmMother():

    def __init__(self,swarm,list_of_callbacks,initial_problem,execute_only=None,database_table = None,database_conn = None):
        self.actions = list_of_callbacks
        self.swarm = swarm
        self.problem = initial_problem
        self.execute_only = execute_only
        self.time_measurements = []
        self.time_statistics_for_problem = dict()
        pass

    def start(self,in_background = False):
        if in_background:
            thread = threading.Thread(target=self.__execute)   
            thread.start()   
            return None
        else:
            return self.__execute()

    def __execute(self):

        for n in range(len(self.actions)):
            action = self.actions[n]
            problem = self.problem
            self.swarm.set_new_task(action)
            print("for action {}, len of problems {}. Self execute: {}".format(action,len(problem),self.execute_only))
            if self.execute_only != None:
                self.swarm.pass_problems(problem[:self.execute_only])
            else:
                self.swarm.pass_problems(problem[:])
            
            done = 0
            start = 0
            amount = 0
            start_time = time.time()
            process = True
            self.swarm.start_swarm()
            done_time = 0
            while(process):         
                prev_done = done
                amount, done = self.swarm.get_current_status()
                # check if watchdogs are feeded
                result=self.swarm.check_watchdogs()
                self.swarm.wakeup_stopped_workers(result)
                
                if amount == done:
                    process = False
                pass
            extime = time.time() - start_time
            print(type(amount))
            
            if amount!= 0 :
                print("Processed {} for {} in {}s. Avg time: {}".format(amount,action,extime,extime/amount)) 
                    
            self.problem=self.swarm.get_results()   

        return self.problem

    def print_status(self):
        done,limit=self.swarm.get_status()
        text_list = []
        for n in range(len(limit)):
            text_list.append("Thread {} done {} from {}".format(n,done[n],limit[n]))
           
        print(*text_list,sep='\n',end='\r')
            
    def get_statistics(self):
        return self.time_statistics_for_problem

    def kill(self):
        self.swarm.kill_swarm()

class Swarm():

    def __init__(self,size_of_swarm = 10):
        self.n_workers = size_of_swarm
        self.workers = []
        self.watchdogs = []
        for unit in range(size_of_swarm):
            self.watchdogs.append(Watchdog())
            self.workers.append(Worker(unit+1,self.watchdogs[unit]))
        
    def stop_swarm(self):
        for worker in self.workers :
            worker.stop()

    def kill_swarm(self):
        for worker in self.workers :
            worker.kill()

    def start_swarm(self):
        for worker in self.workers :
            worker.start()
    
    def set_new_task(self,target):
        for worker in self.workers :
            worker.set_task(target)

    def pass_problems(self,problems):
        rest = len(problems)/self.n_workers
        step =int(len(problems)/self.n_workers)
        if step < 1:
            step = 1

        for n in range(self.n_workers):
            if n == self.n_workers-1:
                sub_lists = problems[n*step:]
            else:
                print(step,n*step,(n+1)*step)
                sub_lists = problems[n*step:(n+1)*step]
            self.workers[n].set_problems(sub_lists)
        pass
    
    def get_current_status(self):
        done = 0 
        amount = 0
        for n in range(self.n_workers):
            a,d = self.workers[n].get_status()
            amount += a
            done += d
        return (amount,done)

    def get_status(self):
        done = []
        amount = []
        for n in range(self.n_workers):
            a,d = self.workers[n].get_status()
            amount.append(a) 
            done.append(d)
        return (amount,done)

    def get_results(self): # assuming the monotask swarm
        results = []
        for n in range(self.n_workers):
            results.extend(self.workers[n].get_result())
        return results

    def check_watchdogs(self):
        results = []
        for n in range(self.n_workers):
            results.append(self.watchdogs[n].getting_hungry())
        return results

    def wakeup_stopped_workers(self,results_from_watchdogs):
        for n in range(self.n_workers):
            if results_from_watchdogs[n] == False:
                
                prev_done=self.workers[n].done
                prev_amount=self.workers[n].amount
                prev_problem_list=self.workers[n].problems_list
                
                self.workers[n].kill()
                self.workers[n] = Worker(n,self.watchdogs[n])
                self.workers[n].set_problems(prev_problem_list)
                self.workers[n].done = prev_done

                self.workers[n].start()

class Watchdog():

    def __init__(self):
        self.hunger = 1000
        self.feeding_time=time.time()
        pass

    def feed_me(self):
        self.feeding_time=time.time()
        pass

    def getting_hungry(self):
        if self.hunger < self.feeding_time-time.time():
            return False
        return True


class Worker():

    def __init__(self,n_worker,watchdog_instance):
        self.watchdog = watchdog_instance
        self.call_back = self.dummy_task
        self.stop_worker = True
        self.kill_worker = False
        self.kwargs = None
        self.worker_number = n_worker
        self.amount = 0
        self.done = 0
        self.problems_list = []
        self.thread = threading.Thread(target=self.__execute)
        self.thread.start()
        self.storage = []
        pass

    def __execute(self):
        while(not self.kill_worker):
            if not self.stop_worker:
                if self.done < self.amount:
                    self.storage[self.done] = self.call_back(self.problems_list[self.done])
                    self.done+=1
                
                else:
                    print(self.worker_number,"finishes one {} of {}".format(self.done,self.amount))
                    self.stop()
            self.watchdog.feed_me()
        pass

    def start(self):
        self.stop_worker = False
        
    def stop(self):
        self.stop_worker = True

    def kill(self):
        self.kill_worker = True
        self.thread.join()

    def dummy_task(self,problem):
        print("I am solving: ",problem)
        pass

    def set_task(self,task_func,kwargs = None):
        self.stop_worker = True
        self.kwargs = kwargs
        self.call_back = task_func
    
    def get_result(self):
        ret = []
        if len(self.storage) > 0:
            if type(self.storage[0]) is list:
                print(type(self.storage[0]),type(self.storage[0]) is list)
                for n_storage in self.storage:
                    if n_storage != None:
                        for element in n_storage:
                            ret.append(element)
            else:
                ret = self.storage
        return ret

    def set_problems(self,problems_list):
        self.problems_list = problems_list
        self.amount = len(problems_list)
        self.storage = [None]* self.amount 
        self.done = 0

    def get_status(self):
        return (self.amount,self.done)

#####################
