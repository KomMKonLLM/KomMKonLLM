# Combinatorial Methods for Consistency Testing of Large Language Models

This repository contains the implementation of our methodology for combinatorial 
consistency testing of large language models.

**Note that the implementation is currently in the early stages of development; 
this repository will be continually updated to include the results of our work 
as soon as they are ready for public release.**

## Who is KomMKonLLM for?

Our work on the consistency of large language models is not only aimed at 
science and research, but also in particular at companies that (want to) 
integrate or use LLMs in their product development or services and want to 
ensure that a certain degree of consistency - and in a wider sense accuracy - of 
the results is given.

## What does consistency testing mean?

Consistency testing of LLMs addresses the problem of ensuring that LLMs respond 
reliably to different inputs. Since LLMs often have complex and opaque 
structures, they can give inconsistent or unexpected answers to similar inputs. 
These inconsistencies make it difficult to use LLMs in applications where 
reliability is crucial. The challenge is to develop suitable test methods that 
systematically evaluate the consistency of the models.

## Challenges

Especially when testing the semantic complexity of LLMs, it is extremely 
challenging to cover the many possible variations in the formulation of input 
queries. We will therefore use automated methods of combinatorial testing, which 
have the advantage of covering the modelled input space (in this case a written 
sentence and the ways of formulating it) to a certain predetermined degree - in 
a certain combinatorial sense.

## How does it work?

We want to create a server solution that automatically creates consistency tests 
for LLMs using combinatorial methods, executes them on LLM instances via open 
interfaces and can also display the results in a prepared form. Together with an 
integrated repository of test cases, this offers a solution for combinatorial 
testing of the consistency of LLMs.

## Who is behind the project?

KomMKonLLM is a project funded by [netidee](https://www.netidee.at/kommkonllm) and implemented by the [MATRIS Research Group](https://matris.sba-research.org/) of SBA Research.
