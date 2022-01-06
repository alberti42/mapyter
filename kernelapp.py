from .kernel import MatlabKernel2

from ipykernel.kernelapp import IPKernelApp

class MatlabKernel2App(IPKernelApp):
    """The launcher application."""

    @classmethod
    def launch_instance(cls):
        super().launch_instance(kernel_class=MatlabKernel2)