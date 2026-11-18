from UPISAS.strategy import Strategy

MIN_TRIPS = 50          
LEARN_WINDOWS = 4       
TOLERANCE = 1.2         
NORMAL = {"re_route_every_ticks": 30, "freshness_cut_off_value": 300}
REACTIVE = {"re_route_every_ticks": 10, "freshness_cut_off_value": 500}


def window_overhead(earlier, later):
    trips = later["total_trips"] - earlier["total_trips"]
    total_later = later["total_trip_overhead_average"] * (later["total_trips"] + 1)
    total_earlier = earlier["total_trip_overhead_average"] * (earlier["total_trips"] + 1)
    return (total_later - total_earlier) / trips


class CC2Baseline(Strategy):
    def __init__(self, exemplar):
        super().__init__(exemplar)
        self.mode = None       
        self.window_start = None
        self.learned = []       
        self.normal = None       

    def analyze(self):
        stats = self.knowledge.monitored_data["car_stats"][-1]
        if self.mode is None:
            self.mode = "normal"
            return True                               

        if self.window_start is None:
            self.window_start = stats
            return False
        if stats["total_trips"] - self.window_start["total_trips"] < MIN_TRIPS:
            return False

        overhead = window_overhead(self.window_start, stats)
        self.window_start = stats

        if self.normal is None:                      
            self.learned.append(overhead)
            if len(self.learned) == LEARN_WINDOWS:
                self.normal = sum(self.learned) / LEARN_WINDOWS
                print(f"[Baseline] normal overhead level: {self.normal:.3f}")
            return False

        wanted = "reactive" if overhead > TOLERANCE * self.normal else "normal"
        print(f"[Baseline] step {stats['step']}: window overhead {overhead:.3f}, mode {wanted}")
        if wanted == self.mode:
            return False
        self.mode = wanted
        return True

    def plan(self):
        new_config = dict(self.knowledge.monitored_data["configs"][-1])
        new_config.update(REACTIVE if self.mode == "reactive" else NORMAL)
        self.knowledge.plan_data = new_config
        return True
