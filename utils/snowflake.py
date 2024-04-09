"""Snowflake ID generator for Django models"""

import time

class Snowflake:
    """Snowflake ID generator for Django models"""

    def __init__(self, worker_id, datacenter_id):
        self.worker_id = worker_id
        self.datacenter_id = datacenter_id
        self.sequence = 0
        self.timestamp = -1

        self.twepoch = 1288834974657 
        self.datacenter_bits = 5
        self.worker_bits = 5
        self.sequence_bits = 12

        self.max_worker_id = -1 ^ (-1 << self.worker_bits)
        self.max_datacenter_id = -1 ^ (-1 << self.datacenter_bits)

        self.worker_id_shift = self.sequence_bits
        self.datacenter_id_shift = self.sequence_bits + self.worker_bits
        self.timestamp_shift = (
            self.sequence_bits + self.worker_bits + self.datacenter_bits
        )
        self.sequence_mask = -1 ^ (-1 << self.sequence_bits)

        if (
            self.worker_id > self.max_worker_id
            or self.datacenter_id > self.max_datacenter_id
        ):
            raise ValueError("Worker ID or Datacenter ID is greater than max")

    def generate_id(self):
        now = int(time.time() * 1000)

        if now < self.timestamp:
            raise ValueError("Clock moved backwards")

        if now == self.timestamp:
            self.sequence = (self.sequence + 1) & self.sequence_mask
            if self.sequence == 0:
                now = self.wait_next_millis(now)
        else:
            self.sequence = 0

        self.timestamp = now

        snowflake_id = (
            ((now - self.twepoch) << self.timestamp_shift)
            | (self.datacenter_id << self.datacenter_id_shift)
            | (self.worker_id << self.worker_id_shift)
            | self.sequence
        )

        return snowflake_id

    def wait_next_millis(self, current_time):
        while current_time <= self.timestamp:
            current_time = int(time.time() * 1000)
        return current_time
