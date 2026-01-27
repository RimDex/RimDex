---
title: Downloading and Installing
parent: User Guide
nav_order: 1
permalink: user-guide/downloading-and-installing
---

# Downloading and Installing
{: .no_toc}

{: .warning }

> Most users should be utilizing [pre-built releases](https://github.com/RimDex/RimDex/releases) and **_not_** downloading the repository code from `Code > Download ZIP`. This option downloads the source code which is not compiled. You only need the source code if you plan on contributing, building RimDex yourself, or running RimDex via a Python interpreter.

There are two types of RimDex releases. Stable releases, and edge releases. Edge releases come out much more often then stable releases, but are more likely to have bugs.

When downloading a release, make sure to select the file more appropriate for your operating system, CPU architecture, and needs. Launch instructions may be platform specific.

[Stable Release][Stable Release]{: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 }
[Edge Release][Edge Release]{: .btn .fs-5 .mb-4 .mb-md-0 }

## Table of Contents
{: .no_toc .text-delta }

1. TOC
{:toc}

## Windows
{: .d-inline-block}

Windows
{: .label .label-blue }

{: .important }
> On Windows, the executable RimDex.exe may sometimes be incorrectly flagged by your anti-virus solution such as Windows Defender and deleted.
>
> Unfortunately this is a side effect of using [Nuikta](https://nuitka.net/) to compile a Python program into an easy to distribute executable, and not signing it. Signing the release costs a significant amount of money and is a re-occuring cost which is infeasible for us. It is safe to override your anti-virus to allow RimDex. If you are unsure about this, feel free to scan the executable using [Virus Total](https://www.virustotal.com/gui/) which will give you the opinion of multiple anti-virus solutions and then form your own opinion.



- Download and extract the `Windows x86-64` release
- Run the executable: `RimDex.exe`

![](../assets/images/previews/windows_preview.png)

## macOS
{: .d-inline-block}

macOS
{: .label .label-red }

{: .important }
> You may get an error saying that RimDex is "damaged" from Gatekeeper.
> Apple has it's own Runtime Protection called [Gatekeeper](https://support.apple.com/guide/security/gatekeeper-and-runtime-protection-sec5599b66df/web) that can cause issues when trying to run RimDex (or execute dependent libs)!
> You can circumvent this issue by using `xattr` command to manually whitelist:
>
>     xattr -d com.apple.quarantine /path/to/RimDex.app
>     xattr -d com.apple.quarantine /path/to/libsteam_api.dylib
>
> Replace `/path/to/` with the actual path where the file/folder is, example:
>
>     xattr -d com.apple.quarantine /Users/John/Downloads/RimDex.app
>
> If you are for some reason trying to run the `i386` build on Apple silicon, don't enable watchdog when running the build through Rosetta

{: .note }

> todds texture tool does not currently (as of May 2023) support Apple silicon (Mac M1/M2 ARM64 CPU).

- Download the and extract the Darwin/macOS release that matches your CPU architecture (ARM64 for Apple Silicon, i386 for Intel)
- Use the `xattr` command to circumvent [Gatekeeper](https://support.apple.com/guide/security/gatekeeper-and-runtime-protection-sec5599b66df/web) and whitelist `RimDex.app` and `libsteam_api.dylib`
- Open the app bundle: `RimDex.app`

<img alt="Macpreview" src="https://github.com/RimDex/RimDex/assets/28567881/7731911b-cc7c-47c8-9c34-6f925fc5b188">

## Linux
{: .d-inline-block}

Linux
{: .label .label-yellow}

{: .warning }

> Certain Linux distros/flavors may not have all the required shared libraries for QT, the graphics library that RimDex uses. Namely, `xcb/libxcb`. If you get an error about loading these when attempting to launch RimDex, you will need to install one or the other. Even after installing the library, there may be additional files that are missing that need to be downloaded separately. For example, `libxcb-cursor-dev`
> 
> The easiest way to find what package has the library you need is the command `apt-file`.
>
> A mismatch of kernel versions may lead to version errors for shared libraries such as `glibc`

{: .important }

> We only release compiled releases for Ubuntu. If you use a different distribution or a special flavor, you may run into unexpected issues. If none of our offered pre-built releases work for you, you may need to [build RimDex yourself from the source code, or run RimDex from the Python interpreter](../development-guide/development-setup).



- Download and extract the appropriate Linux release
- Run the executable: `./RimDex`

<img alt="Linuxpreview" src="https://github.com/RimDex/RimDex/assets/102756485/d26577e4-d488-406b-b9a2-dc2eeea8de25">

[Releases]: https://github.com/oceancabbage/RimDex/releases
[Stable Release]: https://github.com/oceancabbage/RimDex/releases/latest
[Edge Release]: https://github.com/RimDex/RimDex/releases/tag/Edge
