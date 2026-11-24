"""Source text of the retrieval benchmark document (original writing, free to reuse).

Rebuild the PDF with:  pip install reportlab && python -m eval.build_pdf
"""

TITLE = "Operating Systems: Study Notes"

PAGES = [
    ("1. Processes and threads", [
        "A program is a passive file on disk, while a process is a program in execution. Each process has its own address space containing the code, a data section for global variables, a heap for memory allocated at run time, and a stack for function calls and local variables.",
        "The operating system keeps a process control block for every process. It stores the process state, the program counter, the contents of CPU registers, scheduling information such as priority, memory-management information and a list of open files.",
        "A process moves between five states: new, ready, running, waiting and terminated. A running process that requests input or output moves to the waiting state, and returns to the ready queue when the operation completes.",
        "Switching the CPU from one process to another is called a context switch. The kernel saves the state of the old process in its control block and loads the saved state of the new one. Context switches are pure overhead, because no useful work is done while switching.",
        "A thread is the smallest unit of CPU scheduling. Threads of the same process share its code, data and open files but each has its own stack and registers, which makes creating a thread much cheaper than creating a new process.",
    ]),
    ("2. CPU scheduling basics", [
        "The CPU scheduler picks which process in the ready queue runs next. Good scheduling aims for high CPU utilisation and throughput, and low turnaround time, waiting time and response time.",
        "Turnaround time is the total time from submission of a process to its completion. Waiting time is the total time a process spends in the ready queue. Response time is the time from submission until the first response is produced, which matters most for interactive systems.",
        "First-Come, First-Served scheduling runs processes in the order they arrive and is simple to implement with a queue. Its main weakness is the convoy effect: many short processes wait behind one long CPU-bound process, so the average waiting time becomes large.",
        "Shortest-Job-First scheduling always picks the process with the smallest next CPU burst. It is provably optimal for minimising the average waiting time, but the length of the next burst is unknown in advance, so it is usually estimated with an exponential average of previous bursts.",
        "The preemptive version of Shortest-Job-First is called Shortest-Remaining-Time-First. If a new process arrives whose burst is shorter than what remains of the running process, the running process is preempted.",
    ]),
    ("3. More scheduling algorithms", [
        "Round Robin scheduling gives each process a small unit of CPU time called a time quantum, typically 10 to 100 milliseconds. When the quantum expires the process is preempted and put at the back of the ready queue, which makes Round Robin well suited to time-sharing systems.",
        "The choice of quantum matters. If the quantum is very large, Round Robin behaves like First-Come, First-Served. If it is very small, the system spends most of its time on context switches instead of real work.",
        "Priority scheduling runs the process with the highest priority first. A major problem is starvation, where low-priority processes may wait indefinitely. The usual solution is aging: gradually increasing the priority of processes that have waited for a long time.",
        "Multilevel queue scheduling splits the ready queue into separate queues, for example one for interactive foreground processes and one for batch background processes, each with its own scheduling algorithm.",
        "Multilevel feedback queues allow a process to move between queues. A process that uses too much CPU time is moved to a lower-priority queue, while a process that waits too long can be moved up, combining fast response for short jobs with fairness for long ones.",
    ]),
    ("4. Process synchronisation", [
        "A race condition occurs when several processes access shared data at the same time and the final result depends on the exact order in which they run. Race conditions are a common source of bugs that are hard to reproduce.",
        "The part of a program that accesses shared data is called the critical section. A correct solution to the critical-section problem must provide mutual exclusion, progress and bounded waiting.",
        "Peterson's solution is a classic software algorithm that solves the critical-section problem for two processes using a shared turn variable and a flag array. On modern hardware it needs memory barriers to work correctly.",
        "A mutex lock protects a critical section: a process must acquire the lock before entering and release it when leaving. A spinlock is a mutex in which a waiting process loops continuously, which wastes CPU cycles but avoids a context switch when locks are held only briefly.",
        "A semaphore is an integer variable accessed only through two atomic operations, wait and signal. A counting semaphore can range over many values and controls access to a resource with several instances, while a binary semaphore behaves much like a mutex lock.",
        "Classic synchronisation problems used to test new schemes include the bounded-buffer producer-consumer problem, the readers-writers problem and the dining-philosophers problem.",
    ]),
    ("5. Deadlocks", [
        "A deadlock is a situation in which a set of processes are all blocked, each waiting for a resource held by another process in the set, so none of them can ever continue.",
        "Four conditions must hold at the same time for a deadlock to occur: mutual exclusion, hold and wait, no preemption and circular wait. If any one of them is prevented, deadlock cannot happen.",
        "Deadlock prevention breaks one of the four conditions. A common practical technique is to impose a total ordering on all resource types and require every process to request resources in increasing order, which makes circular wait impossible.",
        "Deadlock avoidance requires advance information about the maximum resources each process may need. The Banker's algorithm checks whether granting a request would leave the system in a safe state, meaning there is some order in which every process can finish. If not, the request must wait.",
        "With detection and recovery, the system allows deadlocks to happen, periodically searches a wait-for graph for cycles, and recovers by terminating processes or preempting resources. Many general-purpose operating systems simply ignore deadlocks and leave them to application developers.",
    ]),
    ("6. Memory management", [
        "In contiguous memory allocation each process occupies a single continuous block of memory. Placement strategies include first fit, best fit and worst fit; first fit is usually the fastest.",
        "External fragmentation happens when enough total free memory exists but it is split into small non-adjacent holes. Internal fragmentation is unused memory inside an allocated block, caused by rounding a request up to a fixed block size. Compaction can reduce external fragmentation but is expensive.",
        "Paging avoids external fragmentation by dividing physical memory into fixed-size frames and logical memory into pages of the same size. A page table maps each page number to the frame that holds it.",
        "Every logical address is split into a page number and a page offset. The page number indexes the page table to find the frame, and the offset is added to the frame's start address to form the physical address.",
        "Looking up the page table in memory on every access would double memory access time, so CPUs use a small, fast cache of recent translations called the translation look-aside buffer. A high TLB hit ratio keeps the effective memory access time close to that of a single access.",
    ]),
    ("7. Virtual memory", [
        "Virtual memory lets a process run even when only part of it is in physical memory, so programs can be larger than the available RAM. With demand paging, a page is loaded only when it is first accessed.",
        "Accessing a page that is not in memory causes a page fault. The operating system finds the page on disk, loads it into a free frame, updates the page table and restarts the instruction that caused the fault.",
        "When no frame is free, a page-replacement algorithm chooses a victim page. First-In, First-Out replaces the page that has been in memory the longest. Surprisingly, with FIFO, giving a process more frames can increase the number of page faults, a result known as Belady's anomaly.",
        "The optimal algorithm replaces the page that will not be used for the longest time in the future. It gives the lowest possible page-fault rate but cannot be implemented in practice, so it is used as a benchmark for other algorithms.",
        "Least Recently Used replacement evicts the page that has not been used for the longest time, approximating the optimal algorithm by looking at the past instead of the future. The clock or second-chance algorithm is a cheaper approximation of LRU that uses a reference bit.",
        "Thrashing occurs when a process does not have enough frames for the pages it is actively using, so it spends more time paging than executing. The working-set model prevents thrashing by giving each process enough frames for its recently used pages.",
    ]),
    ("8. File systems", [
        "A file is a named collection of related information stored on secondary storage. The operating system keeps attributes for each file, such as its name, size, owner, permissions and timestamps.",
        "In Unix-like systems each file is described by an inode, which stores its metadata and pointers to its data blocks, but not its name. Directory entries map names to inode numbers, which is how one file can have several hard links.",
        "Contiguous allocation stores a file in consecutive disk blocks, giving fast sequential and direct access but suffering from external fragmentation. Linked allocation chains blocks together with pointers, which removes fragmentation but makes direct access slow.",
        "Indexed allocation keeps all of a file's block pointers in an index block. Unix inodes combine direct pointers with single, double and triple indirect blocks so that small files are fast and very large files are still possible.",
        "A journaling file system writes changes to a log before applying them. After a crash, the system replays or discards incomplete transactions instead of scanning the whole disk, so recovery is fast and the file system stays consistent.",
    ]),
    ("9. Input/output and disks", [
        "With polling, the CPU repeatedly checks a device's status register, which wastes cycles if the device is slow. With interrupts, the device signals the CPU when it is ready, and the CPU runs an interrupt handler.",
        "Direct memory access lets a device controller transfer a whole block of data directly between the device and main memory. The CPU is interrupted only once, when the transfer is complete, instead of once for every byte.",
        "On a hard disk, the time to read data is dominated by seek time, the time to move the arm to the right track, and rotational latency, the time for the right sector to rotate under the head.",
        "Disk scheduling orders pending requests to reduce seek time. Shortest-Seek-Time-First serves the request closest to the current head position but can starve far-away requests. The SCAN or elevator algorithm moves the head from one end of the disk to the other, serving requests along the way, then reverses direction.",
        "Solid-state drives have no moving parts, so seek time and rotational latency do not apply. Flash memory cannot be overwritten in place and wears out after many erase cycles, so SSD controllers use wear levelling to spread writes evenly.",
    ]),
]
