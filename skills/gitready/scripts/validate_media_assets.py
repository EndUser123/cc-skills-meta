#!/usr/bin/env python
"""
validate_media_assets.py - Multi-Domain Media Asset Quality Validation

Validates media assets across 9 quality domains to prevent premature "done" declarations.
Supports all asset types: banners, diagrams, flowcharts, videos, slide decks, player pages.

Quality Domains:
1. Visual Quality - Aesthetic appeal, technical execution
2. Effectiveness/Conversion - Attention-grabbing, engagement potential
3. Platform/GitHub Specifics - Rendering, dimensions, compatibility
4. Brand Identity - Consistency, recognition, differentiation
5. Accessibility - Contrast, screen readers, alt text
6. Performance - File size, format optimization, load time
7. Legal/IP - Licensing, rights, trademarks
8. Maintainability - Reusability, templates, versioning
9. Context Appropriateness - OSS norms, tone, accuracy

Usage:
    python validate_media_assets.py <asset_path> [--asset-type TYPE] [--domains DOMAIN,DOMAIN]
    python validate_media_assets.py assets/banners/myproject_banner.png
    python validate_media_assets.py assets/videos/myproject_explainer.mp4 --asset-type video
    python validate_media_assets.py assets/banners/myproject_banner.png --fail-on-issues
    python validate_media_assets.py assets/banners/myproject_banner.png --domains visual,platform

Environment:
    Z_AI_API_KEY - Z.ai API key for vision analysis (optional, enhances validation)
"""

from __future__ import annotations

import argparse
import base64
import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import httpx
from PIL import Image


class Colors:
    """ANSI color codes for terminal output."""

    BLUE = "\033[0;34m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[0;31m"
    CYAN = "\033[0;36m"
    BOLD = "\033[1m"
    NC = "\033[0m"  # No Color


def log_info(msg: str) -> None:
    """Print info message."""
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")


def log_success(msg: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}[✓]{Colors.NC} {msg}")


def log_warning(msg: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}[!]{Colors.NC} {msg}")


def log_error(msg: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}[✗]{Colors.NC} {msg}")


def log_manual(msg: str) -> None:
    """Print manual check required message."""
    print(f"{Colors.CYAN}[◐]{Colors.NC} {msg}")


class AssetType(Enum):
    """Supported media asset types."""

    BANNER = "banner"
    DIAGRAM = "diagram"
    FLOWCHART = "flowchart"
    VIDEO = "video"
    SLIDES = "slides"
    PLAYER_PAGE = "player_page"

    @classmethod
    def from_path(cls, path: Path) -> AssetType:
        """Detect asset type from file path."""
        suffix = path.suffix.lower()
        parent = path.parent.name.lower()

        if "banner" in path.name.lower() or parent == "banners":
            return cls.BANNER
        elif "video" in parent or suffix in [".mp4", ".mov", ".webm"]:
            return cls.VIDEO
        elif "slides" in parent or suffix == ".pdf":
            return cls.SLIDES
        elif "flowchart" in path.name.lower() or "workflow" in path.name.lower():
            return cls.FLOWCHART
        elif "diagram" in path.name.lower() or "architecture" in path.name.lower():
            return cls.DIAGRAM
        elif "video.html" in path.name or path.name == "video.html":
            return cls.PLAYER_PAGE
        else:
            # Default to banner for images
            if suffix in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
                return cls.BANNER
            raise ValueError(f"Cannot detect asset type from path: {path}")


class QualityDomain(Enum):
    """Quality domains for media asset validation."""

    VISUAL_QUALITY = "visual"
    EFFECTIVENESS = "effectiveness"
    PLATFORM = "platform"
    BRAND = "brand"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"
    LEGAL = "legal"
    MAINTAINABILITY = "maintainability"
    CONTEXT = "context"

    def description(self) -> str:
        """Get domain description."""
        descriptions = {
            QualityDomain.VISUAL_QUALITY: "Visual quality (readability, professionalism, appeal)",
            QualityDomain.EFFECTIVENESS: "Effectiveness (attention-grabbing, engagement)",
            QualityDomain.PLATFORM: "Platform compatibility (GitHub rendering, dimensions)",
            QualityDomain.BRAND: "Brand identity (consistency, recognition)",
            QualityDomain.ACCESSIBILITY: "Accessibility (contrast, screen readers)",
            QualityDomain.PERFORMANCE: "Performance (file size, format, load time)",
            QualityDomain.LEGAL: "Legal/IP (licensing, rights, trademarks)",
            QualityDomain.MAINTAINABILITY: "Maintainability (templates, reusability)",
            QualityDomain.CONTEXT: "Context appropriateness (OSS norms, tone, accuracy)",
        }
        return descriptions[self.value]

    def tier(self) -> str:
        """Get validation tier (automated, vision, manual)."""
        tiers = {
            QualityDomain.VISUAL_QUALITY: "vision",
            QualityDomain.EFFECTIVENESS: "manual",
            QualityDomain.PLATFORM: "automated",
            QualityDomain.BRAND: "vision",
            QualityDomain.ACCESSIBILITY: "automated",
            QualityDomain.PERFORMANCE: "automated",
            QualityDomain.LEGAL: "manual",
            QualityDomain.MAINTAINABILITY: "automated",
            QualityDomain.CONTEXT: "vision",
        }
        return tiers[self]


@dataclass
class DomainCheckResult:
    """Result of a single domain check."""

    domain: QualityDomain
    passed: bool
    score: int | None = None  # 1-10 for vision checks
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    manual_checks: list[str] = field(default_factory=list)
    tier: str = "automated"

    def is_complete(self) -> bool:
        """Check if this domain has been fully validated."""
        if self.tier == "manual":
            return (
                len(self.manual_checks) == 0
            )  # Manual checks are done when list is empty
        return self.passed


@dataclass
class AssetValidationResult:
    """Complete validation result for a media asset."""

    asset_path: str
    asset_type: AssetType
    domain_results: dict[QualityDomain, DomainCheckResult]
    overall_passed: bool = False
    completion_percentage: float = 0.0

    def calculate_completion(self) -> None:
        """Calculate what percentage of domains are complete."""
        if not self.domain_results:
            self.completion_percentage = 0.0
            return

        complete_count = sum(1 for r in self.domain_results.values() if r.is_complete())
        self.completion_percentage = (complete_count / len(self.domain_results)) * 100

    def is_ready(self) -> bool:
        """Check if asset is ready for deployment (all domains complete)."""
        self.calculate_completion()
        return self.completion_percentage >= 100.0

    def get_pending_domains(self) -> list[QualityDomain]:
        """Get domains that still need validation."""
        return [d for d, r in self.domain_results.items() if not r.is_complete()]

    def get_failed_domains(self) -> list[QualityDomain]:
        """Get domains that failed validation."""
        return [
            d
            for d, r in self.domain_results.items()
            if not r.passed and r.tier != "manual"
        ]


class MediaAssetValidator:
    """Multi-domain media asset validator."""

    # Asset specifications
    SPECS = {
        AssetType.BANNER: {"width": 1200, "height": 630, "max_size": 500_000},
        AssetType.DIAGRAM: {
            "max_width": 1920,
            "max_height": 1080,
            "max_size": 1_000_000,
        },
        AssetType.FLOWCHART: {
            "max_width": 1920,
            "max_height": 1080,
            "max_size": 500_000,
        },
    }

    # Vision API configuration
    VISION_API_URL = "https://api.z.ai/api/anthropic/v1/messages"
    VISION_MODEL = "claude-sonnet-4-20250514"
    VISION_VERSION = "2023-06-01"
    VISION_MAX_TOKENS = 1500

    def __init__(
        self, zai_api_key: str | None = None, domains: list[QualityDomain] | None = None
    ):
        """Initialize media asset validator.

        Args:
            zai_api_key: Z.ai API key for vision analysis. If None, reads from Z_AI_API_KEY env var.
            domains: List of domains to validate. If None, validates all domains.
        """
        self.zai_api_key = zai_api_key or os.getenv("Z_AI_API_KEY")
        self.domains = domains or list(QualityDomain)

    def validate(
        self, asset_path: Path, asset_type: AssetType | None = None
    ) -> AssetValidationResult:
        """Run full multi-domain validation on media asset.

        Args:
            asset_path: Path to media asset file.
            asset_type: Type of asset. If None, auto-detected from path.

        Returns:
            Complete validation results.
        """
        if not asset_type:
            asset_type = AssetType.from_path(asset_path)

        log_info(
            f"{Colors.BOLD}=== Media Asset Validation: {asset_path} ==={Colors.NC}"
        )
        log_info(f"Asset Type: {asset_type.value}")
        log_info(f"Domains: {', '.join(d.value for d in self.domains)}")
        print()

        results: dict[QualityDomain, DomainCheckResult] = {}

        # Run validation for each domain
        for domain in self.domains:
            log_info(f"{Colors.BOLD}--- {domain.description()} ---{Colors.NC}")
            result = self._validate_domain(asset_path, asset_type, domain)
            results[domain] = result
            self._print_domain_result(result)
            print()

        # Calculate completion
        overall_result = AssetValidationResult(
            asset_path=str(asset_path),
            asset_type=asset_type,
            domain_results=results,
        )
        overall_result.calculate_completion()

        # Overall verdict
        self._print_summary(overall_result)

        return overall_result

    def _validate_domain(
        self, asset_path: Path, asset_type: AssetType, domain: QualityDomain
    ) -> DomainCheckResult:
        """Validate a single quality domain."""
        tier = domain.tier()

        if tier == "automated":
            return self._validate_automated(asset_path, asset_type, domain)
        elif tier == "vision":
            return self._validate_vision(asset_path, asset_type, domain)
        else:  # manual
            return self._validate_manual(asset_path, asset_type, domain)

    def _validate_automated(
        self, asset_path: Path, asset_type: AssetType, domain: QualityDomain
    ) -> DomainCheckResult:
        """Run automated technical validation."""
        result = DomainCheckResult(domain=domain, passed=False, tier="automated")

        try:
            if domain == QualityDomain.PLATFORM:
                result = self._check_platform_specs(asset_path, asset_type)
            elif domain == QualityDomain.ACCESSIBILITY:
                result = self._check_accessibility(asset_path)
            elif domain == QualityDomain.PERFORMANCE:
                result = self._check_performance(asset_path)
            elif domain == QualityDomain.MAINTAINABILITY:
                result = self._check_maintainability(asset_path, asset_type)
        except Exception as e:
            result.issues.append(f"Validation error: {e}")
            log_error(f"Error: {e}")

        return result

    def _validate_vision(
        self, asset_path: Path, asset_type: AssetType, domain: QualityDomain
    ) -> DomainCheckResult:
        """Run vision API validation."""
        result = DomainCheckResult(domain=domain, passed=False, tier="vision")

        if not self.zai_api_key:
            result.issues.append(
                "Z_AI_API_KEY not configured - vision analysis skipped"
            )
            result.manual_checks = [
                f"Manually verify {domain.description()}",
                "Consider setting Z_AI_API_KEY for automated vision analysis",
            ]
            log_warning("Z_AI_API_KEY not configured - converting to manual check")
            result.tier = "manual"
            return result

        try:
            # Encode image
            with open(asset_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            # Build prompt based on domain
            prompt = self._build_vision_prompt(asset_type, domain)

            # Call vision API
            response = self._call_vision_api(image_data, prompt)

            if response:
                result.score = response.get("score")
                result.issues.extend(response.get("issues", []))
                result.recommendations.extend(response.get("recommendations", []))
                result.passed = (result.score or 0) >= 6  # Pass threshold
        except Exception as e:
            result.issues.append(f"Vision API error: {e}")
            result.manual_checks = [
                f"Manually verify {domain.description()} (API failed)"
            ]
            log_error(f"Vision API error: {e}")

        return result

    def _validate_manual(
        self, asset_path: Path, asset_type: AssetType, domain: QualityDomain
    ) -> DomainCheckResult:
        """Generate manual checklist for domains requiring human judgment."""
        result = DomainCheckResult(domain=domain, passed=False, tier="manual")

        if domain == QualityDomain.EFFECTIVENESS:
            result.manual_checks = [
                "Does this asset grab attention in a feed/social preview?",
                "Is there a clear call-to-action or value proposition visible?",
                "Would this make you want to click/learn more?",
                "A/B test against alternatives if possible",
            ]
        elif domain == QualityDomain.LEGAL:
            result.manual_checks = [
                "Verify font licenses allow redistribution",
                "Check if any stock images require attribution",
                "Confirm no trademarked logos/brands without permission",
                "Verify CC/MIT/Apache license compatibility for assets",
            ]
        elif domain == QualityDomain.CONTEXT:
            result.manual_checks = [
                "Is tone appropriate for OSS community?",
                "Are technical claims accurate?",
                "Does it match project positioning (hobby vs production)?",
                "Would this be acceptable in a professional portfolio?",
            ]

        return result

    def _check_platform_specs(
        self, asset_path: Path, asset_type: AssetType
    ) -> DomainCheckResult:
        """Check platform-specific specifications (dimensions, format)."""
        result = DomainCheckResult(
            domain=QualityDomain.PLATFORM, passed=False, tier="automated"
        )

        if not asset_path.exists():
            result.issues.append(f"File not found: {asset_path}")
            return result

        # Check image dimensions
        try:
            with Image.open(asset_path) as img:
                width, height = img.size
                result.passed = True

                if asset_type in self.SPECS:
                    specs = self.SPECS[asset_type]
                    if "width" in specs and width != specs["width"]:
                        result.issues.append(
                            f"Width {width}px != expected {specs['width']}px"
                        )
                        result.passed = False
                    if "height" in specs and height != specs["height"]:
                        result.issues.append(
                            f"Height {height}px != expected {specs['height']}px"
                        )
                        result.passed = False

                    # Log dimensions
                    if result.passed:
                        log_success(f"Dimensions: {width}x{height} (correct)")
                    else:
                        log_warning(f"Dimensions: {width}x{height}")

        except Exception as e:
            result.issues.append(f"Cannot read image: {e}")
            log_error(f"Cannot read image: {e}")

        return result

    def _check_accessibility(self, asset_path: Path) -> DomainCheckResult:
        """Check accessibility (contrast, file structure)."""
        result = DomainCheckResult(
            domain=QualityDomain.ACCESSIBILITY, passed=False, tier="automated"
        )

        try:
            with Image.open(asset_path) as img:
                img_rgb = img.convert("RGB")

                # Sample center region for contrast check
                width, height = img.size
                sample_region = img_rgb.crop(
                    (width // 4, height // 4, 3 * width // 4, 3 * height // 4)
                )

                # Check if image has reasonable contrast (simplified check)
                try:
                    pixels_data = sample_region.getdata()
                    pixels_list = list(pixels_data)
                except (TypeError, AttributeError):
                    pixels_list = []

                if len(pixels_list) > 100:
                    # Sample 100 pixels for contrast check
                    import random

                    sample = random.sample(pixels_list, min(100, len(pixels_list)))

                    # Calculate luminance variance as contrast proxy
                    luminance = [
                        0.299 * r + 0.587 * g + 0.114 * b for r, g, b in sample
                    ]
                    if luminance:
                        variance = sum(
                            (l - sum(luminance) / len(luminance)) ** 2
                            for l in luminance
                        ) / len(luminance)
                        if variance > 1000:  # Reasonable contrast threshold
                            result.passed = True
                            log_success(
                                f"Contrast check passed (variance: {variance:.0f})"
                            )
                        else:
                            result.issues.append(
                                f"Low contrast detected (variance: {variance:.0f})"
                            )
                            log_warning(f"Low contrast (variance: {variance:.0f})")

        except Exception as e:
            result.issues.append(f"Accessibility check error: {e}")
            log_error(f"Accessibility check error: {e}")

        # Add manual checks
        result.manual_checks = [
            "Verify alt text exists in README/image references",
            "Check color contrast with online tools (WebAIM Contrast Checker)",
            "Test with screen reader if possible",
        ]

        return result

    def _check_performance(self, asset_path: Path) -> DomainCheckResult:
        """Check performance (file size, format)."""
        result = DomainCheckResult(
            domain=QualityDomain.PERFORMANCE, passed=False, tier="automated"
        )

        file_size = asset_path.stat().st_size
        file_size_kb = file_size / 1024

        # Check if size is reasonable
        if file_size_kb < 10:
            result.issues.append(f"File suspiciously small: {file_size_kb:.1f}KB")
            log_warning(f"File size: {file_size_kb:.1f}KB (suspiciously small)")
        elif file_size_kb > 1000:
            result.issues.append(
                f"File large: {file_size_kb:.1f}KB (consider optimization)"
            )
            log_warning(f"File size: {file_size_kb:.1f}KB (large)")
        else:
            result.passed = True
            log_success(f"File size: {file_size_kb:.1f}KB (acceptable)")

        # Check format
        suffix = asset_path.suffix.lower()
        if suffix == ".png":
            result.recommendations.append(
                "Consider WebP for better compression (if GitHub supports it)"
            )
        elif suffix in [".jpg", ".jpeg"]:
            result.recommendations.append(
                "Consider PNG for text-heavy assets (better sharpness)"
            )

        return result

    def _check_maintainability(
        self, asset_path: Path, asset_type: AssetType
    ) -> DomainCheckResult:
        """Check maintainability (source files, templates)."""
        result = DomainCheckResult(
            domain=QualityDomain.MAINTAINABILITY, passed=True, tier="automated"
        )

        # Check for source files
        asset_dir = asset_path.parent
        possible_sources = [
            asset_dir / f"{asset_path.stem}.svg",  # Vector source
            asset_dir / f"{asset_path.stem}.xcf",  # GIMP
            asset_dir / f"{asset_path.stem}.psd",  # Photoshop
            asset_dir / "sources",
            asset_dir / ".." / "sources",
        ]

        source_exists = any(s.exists() for s in possible_sources)
        if source_exists:
            log_success("Source file detected")
        else:
            result.recommendations.append("Store source files for easier updates")
            log_info("No source file detected (recommend storing editable version)")

        # Check if follows naming convention
        if asset_type == AssetType.BANNER and "_banner" not in asset_path.name:
            result.issues.append(
                "Banner doesn't follow naming convention (expected *_banner.png)"
            )
            result.passed = False
        else:
            log_success("Naming convention followed")

        return result

    def _build_vision_prompt(self, asset_type: AssetType, domain: QualityDomain) -> str:
        """Build vision API prompt for specific asset type and domain."""
        base_prompts = {
            (
                QualityDomain.VISUAL_QUALITY,
                AssetType.BANNER,
            ): """Analyze this banner image for GitHub repository social preview.

Rate on a scale of 1-10:
1. Text Readability - Is text clear, high contrast, and legible at small sizes?
2. Professionalism - Does it look polished, intentional, and high-quality?
3. Visual Appeal - Are colors, layout, and design aesthetically pleasing?
4. Technical Execution - Is there proper alignment, spacing, and composition?

Respond in this format:
SCORE: X/10
ISSUES: [list any issues found]
RECOMMENDATIONS: [list specific improvements]
FEEDBACK: [brief overall assessment]""",
            (
                QualityDomain.BRAND,
                AssetType.BANNER,
            ): """Analyze this banner for brand identity strength.

Rate on a scale of 1-10:
1. Package Name Clarity - Is the package name clearly visible?
2. Brand Recognition - Would this be recognizable as the project's brand?
3. Differentiation - Does it stand out from similar projects?
4. Consistency - Do colors, fonts, and style feel cohesive?

Respond in this format:
SCORE: X/10
ISSUES: [list any brand issues]
RECOMMENDATIONS: [list brand improvements]
FEEDBACK: [brief brand assessment]""",
            (
                QualityDomain.CONTEXT,
                AssetType.BANNER,
            ): """Analyze this banner for open source context appropriateness.

Rate on a scale of 1-10:
1. OSS Community Fit - Is tone appropriate for GitHub/developer audience?
2. Technical Accuracy - Are any technical claims or diagrams accurate?
3. Professional Standards - Would this be acceptable in a production portfolio?
4. Clarity of Purpose - Does it communicate what this project does?

Respond in this format:
SCORE: X/10
ISSUES: [list context issues]
RECOMMENDATIONS: [list context improvements]
FEEDBACK: [brief context assessment]""",
        }

        return base_prompts.get(
            (domain, asset_type),
            f"""Analyze this {asset_type.value} for {domain.description()}.

Rate on a scale of 1-10 and provide specific feedback.

Respond in this format:
SCORE: X/10
ISSUES: [list issues]
RECOMMENDATIONS: [list improvements]
FEEDBACK: [assessment]""",
        )

    def _call_vision_api(self, image_data: str, prompt: str) -> dict[str, Any] | None:
        """Call Z.ai Vision API for image analysis."""
        headers = {
            "x-api-key": self.zai_api_key,
            "anthropic-version": self.VISION_VERSION,
            "content-type": "application/json",
        }

        payload = {
            "model": self.VISION_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            "max_tokens": self.VISION_MAX_TOKENS,
        }

        try:
            log_info("Calling Vision API...")
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self.VISION_API_URL, headers=headers, json=payload
                )

                if response.status_code == 200:
                    data = response.json()
                    content = ""
                    for block in data.get("content", []):
                        if block.get("type") == "text":
                            content += block.get("text", "")

                    return self._parse_vision_response(content)
                else:
                    log_error(f"API Error: HTTP {response.status_code}")
                    return None
        except httpx.TimeoutException:
            log_error("API timeout (30s)")
            return None
        except Exception as e:
            log_error(f"API Error: {e}")
            return None

    def _parse_vision_response(self, content: str) -> dict[str, Any]:
        """Parse structured response from vision API."""
        result = {
            "score": None,
            "issues": [],
            "recommendations": [],
            "feedback": content,
        }

        for line in content.split("\n"):
            if line.startswith("SCORE:"):
                try:
                    score_str = line.split(":")[1].strip().split("/")[0]
                    result["score"] = int(score_str)
                    log_success(f"Quality Score: {score_str}/10")
                except (ValueError, IndexError):
                    pass
            elif line.startswith("ISSUES:"):
                issues = line.split(":", 1)[1].strip()
                if issues and issues != "[]":
                    result["issues"] = [i.strip("- ") for i in issues.split(",")]
            elif line.startswith("RECOMMENDATIONS:"):
                recs = line.split(":", 1)[1].strip()
                if recs and recs != "[]":
                    result["recommendations"] = [r.strip("- ") for r in recs.split(",")]

        return result

    def _print_domain_result(self, result: DomainCheckResult) -> None:
        """Print result for a single domain."""
        if result.tier == "manual":
            log_manual(f"{Colors.CYAN}Manual verification required{Colors.NC}")
            for check in result.manual_checks:
                print(f"  □ {check}")
        elif result.passed:
            log_success(f"{Colors.GREEN}PASSED{Colors.NC}")
            if result.score is not None:
                print(f"  Score: {result.score}/10")
        else:
            log_error(f"{Colors.RED}FAILED{Colors.NC}")
            for issue in result.issues:
                print(f"  ✗ {issue}")

        if result.recommendations:
            log_info("Recommendations:")
            for rec in result.recommendations:
                print(f"  → {rec}")

    def _print_summary(self, result: AssetValidationResult) -> None:
        """Print validation summary."""
        print(f"{Colors.BOLD}{'=' * 60}{Colors.NC}")
        log_info(f"{Colors.BOLD}Validation Summary{Colors.NC}")
        print(f"{Colors.BOLD}{'=' * 60}{Colors.NC}")

        result.calculate_completion()

        # Completion status
        print(f"\nCompletion: {result.completion_percentage:.0f}%")

        if result.is_ready():
            log_success(
                f"{Colors.GREEN}{Colors.BOLD}ASSET READY FOR DEPLOYMENT{Colors.NC}"
            )
        else:
            pending = result.get_pending_domains()
            log_warning(
                f"Pending domains ({len(pending)}): {', '.join(d.value for d in pending)}"
            )

        # Failed domains
        failed = result.get_failed_domains()
        if failed:
            log_error(f"Failed domains: {', '.join(d.value for d in failed)}")

        # Manual checklist
        all_manual = [d for d, r in result.domain_results.items() if r.tier == "manual"]
        if all_manual:
            print(
                f"\n{Colors.BOLD}Manual Checklist ({len(all_manual)} domains):{Colors.NC}"
            )
            for domain in all_manual:
                domain_result = result.domain_results[domain]
                print(f"\n{Colors.CYAN}{domain.value}:{Colors.NC}")
                for i, check in enumerate(domain_result.manual_checks, 1):
                    print(f"  □ {i}. {check}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-domain media asset quality validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Quality Domains:
  visual       Visual quality (readability, professionalism, appeal)
  effectiveness Effectiveness (attention-grabbing, engagement) [manual]
  platform      Platform compatibility (GitHub rendering, dimensions)
  brand         Brand identity (consistency, recognition)
  accessibility Accessibility (contrast, screen readers)
  performance   Performance (file size, format, load time)
  legal         Legal/IP (licensing, rights, trademarks) [manual]
  maintainability Maintainability (templates, reusability)
  context       Context appropriateness (OSS norms, tone, accuracy)

Examples:
  %(prog)s assets/banners/myproject_banner.png
  %(prog)s assets/videos/myproject_explainer.mp4 --asset-type video
  %(prog)s assets/banners/myproject_banner.png --domains visual,platform
  %(prog)s assets/banners/myproject_banner.png --fail-on-issues
        """,
    )
    parser.add_argument("asset_path", type=Path, help="Path to media asset file")
    parser.add_argument(
        "--asset-type",
        choices=[t.value for t in AssetType],
        help="Asset type (auto-detected if not specified)",
    )
    parser.add_argument(
        "--domains",
        help="Comma-separated list of domains to validate (default: all)",
    )
    parser.add_argument(
        "--zai-key",
        help="Z.ai API key for vision analysis (or set Z_AI_API_KEY env var)",
    )
    parser.add_argument(
        "--fail-on-issues",
        action="store_true",
        help="Exit with error code if validation fails or is incomplete",
    )

    args = parser.parse_args()

    # Parse domains
    domains = None
    if args.domains:
        try:
            domains = [QualityDomain(d.strip()) for d in args.domains.split(",")]
        except ValueError as e:
            log_error(f"Invalid domain: {e}")
            sys.exit(1)

    # Parse asset type
    asset_type = None
    if args.asset_type:
        asset_type = AssetType(args.asset_type)

    # Validate
    validator = MediaAssetValidator(zai_api_key=args.zai_key, domains=domains)
    result = validator.validate(args.asset_path, asset_type)

    # Exit code
    if args.fail_on_issues:
        if not result.is_ready() or result.get_failed_domains():
            sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
