from inspect import signature
import os

from AIPSData import AIPSCat, AIPSImage, AIPSUVData
from AIPSTask import AIPSList, AIPSTask
from AIPSTV import AIPSTV

# main pyAIPSTask decorator
class pyAIPSTask:
    """
    Decorator class for wrapping AIPS task functions with argument 
    validation, task initialization, and result handling logic. This 
    class is designed to simplify the creation and execution of AIPS 
    tasks by automating argument parsing, input/output data assignment, 
    TV handling, and output data retrieval. It can be used as a 
    decorator on functions that define the main logic for a specific 
    AIPS task.
    Parameters:
        task_name (str): Name of the AIPS task to be executed.
        indata (bool or int, optional): Whether the task requires an 
            input AIPS data object. 
        datain (bool or int, optional): Whether the task requires an 
            input file path. 
        intext (bool, optional): Whether the task requires an input text 
            file.
        calin (bool or int, optional): Whether the task requires a 
            calibration input file. 
        outdisk (bool, optional): Whether the task requires an output 
            disk number.
        outdata (bool or int, optional): Whether the task produces an 
            output AIPS data object. 
        dataout (bool or int, optional): Whether the task produces an 
            output file. 
        outtext (bool, optional): Whether the task produces an output 
            text file.
        sources (bool, optional): Whether the task requires a list of 
            source names.
        srcname (bool, optional): Whether the task requires a single 
            source name.
        calsour (bool, optional): Whether the task requires a list of 
            calibrator sources.
        requires_tv (bool, optional): Whether the task requires an AIPS 
            TV device.
        persistent_tv (bool, optional): Whether the AIPS TV should
            remain open after the task execution.
        create_data (bool or int, optional): Whether the task creates 
            new AIPS data. 
        create_type (str, optional): Type of data created ('UV' for UV 
            data, otherwise image data - preferably 'IM').
    Usage:
        @pyAIPSTask('TASKNAME', indata=True, outdata=True, ...)
        def my_task(task, ...):
            # Set additional task parameters here
            ...
        my_task(indata=..., outdata=..., ...)
    Methods:
        __call__(func): Decorates the given function, handling argument 
            validation, task setup, execution, and output retrieval.
        _assign_data(task, name, kwargs, flag, path=False): Assigns 
            data-related arguments to the task.
        _assign_string(task, name, kwargs, flag): Assigns string 
            arguments to the task.
        _assign_int(task, name, kwargs, flag): Assigns integer 
            arguments to the task.
        _assign_list(task, name, kwargs, flag): Assigns list 
            arguments to the task.
    Raises:
        TypeError: If positional arguments are provided or unexpected 
            keyword arguments are encountered.
    Returns:
        The result of the decorated function, or the created AIPS data 
            object(s) if `create_data` is set.
    """
    def __init__(
        self, task_name, 
        indata=False, datain=False, intext=False, calin=False, 
        outdisk=False, outdata=False, dataout=False, outtext=False,
        sources=False, srcname=False, calsour=False, 
        requires_tv=False, persistent_tv=False,
        create_data=False, create_type='UV'
    ):
        self.task_name = task_name
        self.indata = indata
        self.datain = datain
        self.intext = intext
        self.calin = calin
        self.dataout = dataout
        self.outdata = outdata
        self.outdisk = outdisk
        self.outtext = outtext
        self.sources = sources
        self.srcname = srcname
        self.calsour = calsour
        self.requires_tv = requires_tv
        self.persistent_tv = persistent_tv
        self.create_data = create_data
        self.create_type = create_type

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            # argument filtering
            if args:
                raise TypeError(
                    f'{func.__name__}() only accepts keyword arguments'
                )
            wrapper_args = {'params'} | {
                field for field in [
                    'indata', 'datain', 'intext', 'calin', 
                    'outdisk', 'outdata', 'dataout', 'outtext',
                    'sources', 'srcname', 'calsour'
                ] 
                if getattr(self, field)
            }
            func_args = signature(func).parameters.keys()
            all_args = wrapper_args | func_args
            unexpected_args = [key for key in kwargs if key not in all_args]
            if unexpected_args:
                raise TypeError(
                    f'{func.__name__}() got unexpected keyword argument(s): '
                    f'{", ".join(unexpected_args)}'
                )
            
            # initialize task
            task = AIPSTask(self.task_name)

            # prepare TV
            tv = AIPSTV() if self.requires_tv else None
            if tv: tv.start()
            
            # call main function
            func(task, **{k: v for k, v in kwargs.items() if k in func_args})

            # argument handling
            self._assign_data(task, 'indata', kwargs, self.indata)
            self._assign_data(task, 'datain', kwargs, self.datain, path=True)
            self._assign_data(task, 'intext', kwargs, self.intext)
            self._assign_data(task, 'calin', kwargs, self.calin, path=True)
            self._assign_data(task, 'dataout', kwargs, self.dataout, path=True)
            self._assign_data(task, 'outdata', kwargs, self.outdata)
            self._assign_int(task, 'outdisk', kwargs, self.outdisk)
            self._assign_data(task, 'outtext', kwargs, self.outtext)
            self._assign_list(task, 'sources', kwargs, self.sources)
            self._assign_string(task, 'srcname', kwargs, self.srcname)
            self._assign_list(task, 'calsour', kwargs, self.calsour)

            # parse extra parameters and run task
            parse_params(task, kwargs.get('params'))
            if self.create_data: 
                outdisk = int(
                    task.indisk if not self.outdisk else task.outdisk
                )
                initial = grab_catalogue(outdisk)
            task.go()

            # close TV if needed
            if tv: 
                if self.persistent_tv:
                    input('Press enter to continue...')
                tv.kill()

            # return results
            if self.create_data:
                final = grab_catalogue(outdisk)
                data_class = (
                    AIPSUVData if self.create_type == 'UV' else AIPSImage
                )
                if isinstance(self.create_data, int) and self.create_data > 1:
                    output = compare_catalogues(
                        initial, final, return_multiple=True
                    )
                    return [
                        data_class(
                            obj.name, obj.klass, outdisk, obj.seq
                        )
                        for obj in output
                    ]
                else:
                    output = compare_catalogues(initial, final)
                    return data_class(
                        output.name, output.klass, outdisk, output.seq
                    )

        return wrapper

    # helper methods for argument handling
    def _assign_data(self, task, name, kwargs, flag, path=False):
        if not flag: return
        value = kwargs.get(name)
        if value is None: return

        if isinstance(flag, int) and flag > 1:
            for i in range(flag):
                attr = f'{name if i == 0 else f"{name[0]}{i+1}{name[1:]}" }'
                val = value[i]
                setattr(task, attr, os.path.realpath(val) if path else val)
        else:
            setattr(task, name, os.path.realpath(value) if path else value)

    def _assign_string(self, task, name, kwargs, flag):
        if flag:
            val = kwargs.get(name)
            if val is not None:
                setattr(task, name, str(val))

    def _assign_int(self, task, name, kwargs, flag):
        if flag:
            val = kwargs.get(name)
            if val is not None:
                setattr(task, name, int(val))

    def _assign_list(self, task, name, kwargs, flag):
        if flag:
            val = kwargs.get(name)
            if val is not None:
                val_list = val if isinstance(val, list) else [val]
                setattr(task, name, AIPSList(val_list))

# utility functions
def grab_catalogue(disk):
    # grab catalogue from disk
    return AIPSCat(int(disk))[int(disk)]

def compare_catalogues(catalogue1, catalogue2, return_multiple=False):
    # compare two catalogues
    for catalogue in [catalogue1, catalogue2]:
        for item in catalogue:
            item.pop('date')
            item.pop('time')
    
    new_items = [item for item in catalogue2 if item not in catalogue1]
    if return_multiple:
        return new_items
    else:
        return new_items[0]

def parse_params(task, params):
    # parse parameters
    if params:
        for key, value in params.items():
            if value is None: continue
            if '|' in key:
                temp = getattr(task, key.split('|')[0])
                temp[int(key.split('|')[1])] = value
            else: 
                setattr(task, key, value)

# tasks
@pyAIPSTask('ACCOR', indata=True)
def accor(task, solint):
    task.solint = solint

@pyAIPSTask('ANTAB', indata=True, calin=True)
def antab(task):
    pass

@pyAIPSTask('APCAL', indata=True)
def apcal(task):
    pass

@pyAIPSTask('BPASS', indata=True, calsour=True)
def bpass(task):
    pass

@pyAIPSTask('CCMRG', indata=True)
def ccmrg(task):
    pass

@pyAIPSTask('CLCAL', indata=True, sources=True, calsour=True)
def clcal(task, snver, invers, gainver, gainuse, refant=-1):
    task.snver = snver
    task.invers = invers
    task.gainver = gainver
    task.gainuse = gainuse
    task.refant = refant

@pyAIPSTask('CVEL', indata=True, sources=True, create_data=True)
def cvel(task, freqid=1):
    task.freqid = freqid

@pyAIPSTask('FITLD', datain=True, outdisk=True, sources=True, create_data=True)
def fitld(task, clint):
    task.clint = clint

@pyAIPSTask('FITTP', indata=True, dataout=True)
def fittp(task, doall=1):
    task.doall = doall

@pyAIPSTask('FRING', indata=True, calsour=True)
def fring(task):
    pass

@pyAIPSTask(
    'IMAGR', indata=True, outdisk=True, srcname=True, create_data=2, 
    create_type='IM'
)
def imagr(task, cellsize, imsize, niter=0):
    if isinstance(cellsize, float):
        task.cellsize = AIPSList([cellsize, cellsize])
    else:
        task.cellsize = AIPSList([*cellsize])
    if isinstance(imsize, int):
        task.imsize = AIPSList([imsize, imsize])
    else:
        task.imsize = AIPSList([*imsize])
    task.niter = niter

@pyAIPSTask('INDXR', indata=True)
def indxr(task, solint):
    task.cparm[3] = solint

@pyAIPSTask('MSORT', indata=True, outdata=True, create_data=True)
def msort(task, sort):
    task.sort = sort

@pyAIPSTask(
    'POSSM', indata=True, sources=True, requires_tv=True, persistent_tv=True
)
def possm(task):
    pass

@pyAIPSTask('SETJY', indata=True, sources=True)
def setjy(task):
    pass

@pyAIPSTask('SNCOR', indata=True, sources=True)
def sncor(task, opcode, snver=0):
    task.opcode = opcode
    task.snver = snver

@pyAIPSTask('SNEDT', indata=True, requires_tv=True)
def snedt(task, invers):
    task.invers = invers

@pyAIPSTask('SPLAT', indata=True, outdisk=True, sources=True, create_data=True)
def splat(task, mode='cross'):
    task.aparm[5] = {
        'cross': 0,
        'both': 1,
        'auto': 2
    }[mode]

@pyAIPSTask('SPLIT', indata=True, outdisk=True, sources=True, create_data=True)
def split(task, mode='cross'):
    task.aparm[5] = {
        'cross': 0,
        'both': 1,
        'auto': 2
    }[mode]

@pyAIPSTask('TABED', indata=True, outdata=True)
def tabed(task):
    pass

@pyAIPSTask('TACOP', indata=True, outdata=True)
def tacop(task, inext, invers, outvers, ncount=1):
    task.inext = inext
    task.invers = invers
    task.outvers = outvers
    task.ncount = ncount

@pyAIPSTask('TBIN', intext=True, outdata=True)
def tbin(task):
    pass

@pyAIPSTask('UVFLG', indata=True, intext=True)
def uvflg(task, outfgver):
    task.outfgver = outfgver

@pyAIPSTask(
    'UVPLT', indata=True, sources=True, requires_tv=True, persistent_tv=True
)
def uvplt(task):
    pass

@pyAIPSTask(
    'VPLOT', indata=True, sources=True, requires_tv=True, persistent_tv=True
)
def vplot(task):
    pass
