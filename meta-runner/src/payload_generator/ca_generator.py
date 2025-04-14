"""CA generator wrapper implementations.

This module contains interfaces to various covering array generators.
To add your own wrapper, create a subclass of CaGenerator and override
at least the generate() method, which takes a list of lists (synonyms)
and a strength as input and returns the path to the generated CA
(which should be a headerless, quote-less CSV) as well as the number
of rows.
Optionally, you may also override the read() method, which is used to
return rows from the generated CA.
Finally, add your generator to CaGenerator::get_generator()."""

from os import getenv, access, X_OK
import subprocess
import logging
from pathlib import Path
from typing import Generator
import re

class CaGenerator:
    """Abstract superclass/interface for CA generator implementations.

    This class additionally contains some static helper methods."""

    @staticmethod
    def get_generator():
        """Return a CaGenerator subclass instance.

        The correct generator is selected through the CA_GENERATOR
        environment variable.
        The path to the generator executable is taken from the
        CA_GENERATOR_PATH environment variable."""

        gen_name = getenv('CA_GENERATOR', '').upper()
        gen_path = Path(getenv('CA_GENERATOR_PATH', '/dev/null'))

        # Check if the executable exists (and is executable)
        if not (gen_path.is_file() and access(gen_path, X_OK)):
            raise ValueError('Invalid CA generator executable, check '
                             'CA_GENERATOR_PATH env variable')

        match gen_name:
            case 'CAGEN':
                return CaGenExecutor(gen_path)
            case 'ACTS':
                return ActsExecutor(gen_path)
            case 'PICT':
                return PictExecutor(gen_path)
            case _:
                raise ValueError('Invalid CA generator type, check '
                                 'CA_GENERATOR environment variable')

    @staticmethod
    def cardinalities(synonyms: list[list[str]], as_str: bool = False) -> list[int] | str:
        """Computes the cardinalities, i.e. the number of synonyms per entry."""
        lens = [len(x) for x in synonyms]
        if as_str:
            return ','.join([str(x) for x in lens])
        return lens

    @staticmethod
    def ca_filename(synonyms: list[list[str]], strength: int) -> Path:
        """Generates a sane filename for a CA.

        It is not mandatory to use this method, only recommended."""
        cardinalities = CaGenerator.cardinalities(synonyms, as_str=True)
        filename = f'ca-t{strength}-{cardinalities}.csv'
        assert len(filename) <= 255 # POSIX limit, not sure if valid on each system
        return Path(filename)

    def generate(self, synonyms: list[list[str]], strength: int) -> tuple[Path, int]:
        """Generate a CA and return its location and number of rows."""
        raise NotImplementedError("CaGenerator::generate() is abstract")

    def read(self, synonyms: list[list[str]], strength: int) -> Generator[str, None, None]:
        """Return rows from the CA, one by one."""
        with open(CaGenerator.ca_filename(synonyms, strength),
                  encoding='utf-8') as fp:
            for line in fp:
                if ',' in line:  # Ignore non-CSV lines
                    yield line

class CaGenExecutor(CaGenerator):
    """Wrap CAgen for CA generation."""
    def __init__(self, gen_path: Path):
        self.gen_path = gen_path

    def generate(self, synonyms: list[list[str]], strength: int) -> tuple[Path, int]:
        """Generate a CA and return its location and number of rows."""
        cardinalities = CaGenerator.cardinalities(synonyms, as_str=True)
        path = CaGenerator.ca_filename(synonyms, strength)
        if not (path.is_file() and path.stat().st_size > len(synonyms)):
            # Only generate the CA if it does not exist yet
            cmd = (f'{self.gen_path} -t {strength} -i {cardinalities} -p -q '
                   f'--randomize -o {path}')
            fipo_proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
            _, errs = fipo_proc.communicate()
            errs = str(errs)
            num_rows = int(re.search(r'\d+', errs).group())
            return path, num_rows
        # Otherwise just open the file and count the lines
        return path, len([self.read(synonyms, strength)])

class PictExecutor(CaGenerator):
    """Wrap PICT for CA generation."""
    def __init__(self, gen_path: Path):
        self.gen_path = gen_path

    def create_ipm(self, synonyms: list[list[str]], strength: int) -> Path:
        """Create a model file for PICT from synonyms."""
        cardinalities = CaGenerator.cardinalities(synonyms, as_str=False)
        ca_path = CaGenerator.ca_filename(synonyms, strength)
        ipm_path = Path(ca_path.parent, ca_path.stem + '.ipm')
        with ipm_path.open(mode='w', encoding='utf-8') as fp:
            for i, v_i in enumerate(cardinalities):
                fp.write(f'P{i},{",".join([str(x) for x in range(v_i)])}\n')
        return ipm_path

    def generate(self, synonyms: list[list[str]], strength: int) -> tuple[Path, int]:
        """Generate a CA and return its location and number of rows."""
        path = CaGenerator.ca_filename(synonyms, strength)
        if not (path.is_file() and path.stat().st_size > len(synonyms)):
            # Only generate the CA if it does not exist yet
            cmd = f'{self.gen_path} {self.create_ipm(synonyms, strength)} /o:{strength}'
            pict_proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
            out, _ = pict_proc.communicate()
            lines = out.decode().replace('\t', ',').splitlines()
            have_header = False
            num_rows = 0
            with path.open(mode='w', encoding='utf-8') as fp:
                for line in lines:
                    if not have_header:
                        have_header = True
                        continue
                    elif ',' in line:
                        fp.write(f'{line}\n')
                        num_rows += 1
            return path, num_rows

        # Just return information about the cached CA
        return path, len([self.read(synonyms, strength)])

class ActsExecutor(CaGenerator):
    """Wrap ACTS for CA generation."""
    def __init__(self, gen_path: Path):
        self.gen_path = gen_path

    def create_ipm(self, synonyms: list[list[str]], strength: int) -> Path:
        """Create a model file for ACTS from synonyms."""
        cardinalities = CaGenerator.cardinalities(synonyms, as_str=False)
        ca_path = CaGenerator.ca_filename(synonyms, strength)
        ipm_path = Path(ca_path.parent, ca_path.stem + '.txt')
        with ipm_path.open(mode='w', encoding='utf-8') as fp:
            fp.write('[System]\nName: LLMTMP\n\n[Parameter]\n')
            for i, v_i in enumerate(cardinalities):
                fp.write(
                    f'P{i}(int): {",".join([str(x) for x in range(v_i)])}\n'
                )
        return ipm_path

    def generate(self, synonyms: list[list[str]], strength: int) -> tuple[Path, int]:
        """Generate a CA and return its location and number of rows."""
        path = CaGenerator.ca_filename(synonyms, strength)
        if not (path.is_file() and path.stat().st_size > len(synonyms)):
            # Only generate the CA if it does not exist yet
            temp_path = Path(path.parent, path.stem + '.tmp')
            cmd = (f'java -Ddoi={strength} -Doutput=csv -jar {self.gen_path} '
                   f'{self.create_ipm(synonyms, strength)} {temp_path}')
            acts_proc = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
            acts_proc.wait()
            have_header = False
            num_rows = 0
            with temp_path.open(mode='r', encoding='utf-8') as fp_in:
                with path.open(mode='w', encoding='utf-8') as fp_out:
                    for line in fp_in:
                        if not have_header:
                            # ACTS output files have a commented header
                            # first and then a single header line with
                            # parameter names; we want to ignore both
                            if not line.startswith('#'):
                                have_header = True
                            continue
                        if ',' in line:
                            # We need to strip() these because ACTS uses
                            # CRLF line endings, resulting in empty lines
                            fp_out.write(f'{line.strip()}\n')
                            num_rows += 1
            temp_path.unlink(missing_ok=True) # Remove temp file
            return path, num_rows

        # Just return information about the cached CA
        return path, len([self.read(synonyms, strength)])
